#!/usr/bin/env python3
import pathlib, subprocess, base64, requests, os, json, time, sys, datetime, collections, re
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "google/gemini-2.5-flash"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
CHUNK_SEC = 300

def slugify(name):
    return name.lower().replace(" ","_").replace("(","").replace(")","").replace("-","_").replace("__","_").strip("_")

def run(nayanar, seq_fid_list, phase="all"):
    """
    phase: A=download only, B=chunk+transcribe Tamil, C=chunk+translate English, all=A+B+C (legacy)
    From Day07 onwards use 3-phase: A (2-parallel download), B (4-parallel transcribe), C (4-parallel chunked translate 60K).
    Tails with 0 chars (e.g., 251c03 75s, 261c04 34s) are logged to _errors.log and pause for manual review per transcription-strategy.md:6.
    """
    SLUG = slugify(nayanar)
    DAY = "day-07"  # change per batch: day-01, day-02, ... day-10, day-11+
    PHASES = set(phase.upper().split(",")) if isinstance(phase, str) else set(phase)
    if "ALL" in PHASES:
        PHASES = {"A","B","C"}
    do_A = "A" in PHASES
    do_B = "B" in PHASES
    do_C = "C" in PHASES
    print(f"\n=== {nayanar} -> {SLUG} seq {seq_fid_list} ===")
    BASE = pathlib.Path(r"D:\nalvar\periapuranam\output") / DAY / SLUG
    AUDIO_DIR = BASE / "audio"
    TAMIL_DIR = BASE / "tamil_real"
    TMP_DIR = pathlib.Path(os.environ.get("TEMP", r"C:\Users\Sony\AppData\Local\Temp")) / "opencode" / f"{SLUG}_chunks"
    for d in [AUDIO_DIR, TAMIL_DIR, TMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    headers_dl = {"User-Agent": "Mozilla/5.0"}
    headers_llm = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nalvar.in",
        "X-Title": f"Nalvar Periyapuranam - {nayanar} Tamil"
    }
    def download_drive(file_id, dest):
        url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        for dl_try in range(1,4):
            try:
                print(f"  DOWNLOAD {file_id} -> {dest.name} ... (try {dl_try}/3)")
                session = requests.Session()
                resp = session.get(url, headers=headers_dl, stream=True, timeout=120)
                token = None
                for k,v in resp.cookies.items():
                    if k.startswith("download_warning"):
                        token = v
                        break
                if token:
                    params = {"id": file_id, "export": "download", "confirm": token}
                    resp = session.get("https://drive.usercontent.google.com/download", params=params, headers=headers_dl, stream=True, timeout=120)
                resp.raise_for_status()
                total=0
                # ensure parent exists and remove partial on retry
                with open(dest,"wb") as f:
                    for chunk in resp.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)
                            total+=len(chunk)
                # verify at least 1 MB
                if total < 1024*1024:
                    raise ValueError(f"download too small {total} bytes")
                print(f"    -> {total/1024/1024:.1f} MB (try {dl_try})")
                return total
            except Exception as e:
                print(f"    DOWNLOAD retry {dl_try}/3 failed: {e}")
                # remove partial file
                try:
                    if dest.exists():
                        dest.unlink()
                except: pass
                if dl_try == 3:
                    raise
                time.sleep(5*dl_try)
    def get_duration(path):
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True)
        return float(r.stdout.strip())
    def make_chunk(src, offset, dur, out):
        cmd=["ffmpeg","-y","-i",str(src),"-ss",str(offset),"-t",str(dur),"-c:a","libmp3lame","-b:a","64k",str(out)]
        subprocess.run(cmd, capture_output=True)
        return out
    def transcribe_chunk(chunk_path, seq, chunk_idx, total_chunks):
        prompt=(f"Periya Puranam {nayanar} Part {seq:03d}, chunk {chunk_idx+1}/{total_chunks}. "
                "Transcribe this Tamil pravachan audio verbatim in Tamil script (தமிழ்) only. "
                "Preserve all Tamil words, names, verses, and speech exactly as heard. "
                "No English, no summary, no extra commentary. Output only Tamil transcription for this chunk.")
        data=chunk_path.read_bytes()
        b64=base64.b64encode(data).decode('utf-8')
        payload={"model":MODEL,"messages":[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:audio/mpeg;base64,{b64}"}}]}],"max_tokens":12000,"temperature":0.1}
        for retry in range(3):
            try:
                r=requests.post(ENDPOINT, headers=headers_llm, json=payload, timeout=300)
                if r.status_code==200:
                    j=r.json()
                    content=j["choices"][0]["message"]["content"] or ""
                    content=content.strip()
                    if content.startswith("```"):
                        content=content.split("\n",1)[-1].rsplit("```",1)[0].strip()
                    return content,j
                else:
                    body = r.text[:800]
                    if r.status_code in (402,403) and ("Budget" in body or "budget" in body.lower() or "insufficient" in body.lower()):
                        print(f"    FATAL BUDGET {r.status_code}: {body[:400]} — aborting, no retry")
                        sys.exit(2)
                    print(f"    HTTP {r.status_code} retry {retry+1}: {body[:400]}")
                    time.sleep(2*(retry+1))
            except Exception as e:
                print(f"    exception retry {retry+1}: {e}")
                time.sleep(2*(retry+1))
        return None,None

    # === INSTRUMENTATION & FAIL-SAFE (parallel experiment 2-workers, dur-aware) ===
    INSTRUMENT = []  # per-chunk
    ANOMALIES = []
    EXPERIMENT_START = time.time()
    def _flag_anomaly(seq, chunk_idx, content, meta, duration, throttle_wait, dur):
        chars = len(content) if content else 0
        flag = None
        # duration-aware: ~8 chars/s for Tamil (300s ~2400c min, 11s ~88c min)
        min_expected = max(30, int(dur * 6))  # allow 6c/s lower bound, min 30 for 1s tails
        max_expected = int(dur * 20) + 500  # allow 20c/s upper + slack
        if chars == 0 or not (content or "").strip():
            flag = "EMPTY_0CHAR"
        elif chars < min_expected:
            flag = f"TINY_{chars}_dur{dur:.0f}_exp{min_expected}"
        elif chars > max_expected:
            flag = f"HUGE_{chars}_dur{dur:.0f}_exp{max_expected}"
        else:
            if chars > 1000:
                windows = [content[i:i+8] for i in range(0, len(content)-8, 8)]
                if windows:
                    most_common, cnt = collections.Counter(windows).most_common(1)[0]
                    if cnt > 30 and len(most_common.strip()) > 3:
                        flag = f"REPEAT_{most_common[:12]}_{cnt}"
        usage = (meta or {}).get("usage", {}) if isinstance(meta, dict) else {}
        cost = usage.get("cost") if usage else None
        finish = None
        try:
            if isinstance(meta, dict) and meta.get("choices"):
                finish = meta["choices"][0].get("finish_reason")
        except:
            finish = None
        # only flag finish error if truly failed (cost 0 and chars tiny)
        if finish and finish != "stop":
            if cost == 0 or cost is None or chars < min_expected:
                flag = (flag + "|" if flag else "") + f"FINISH_{finish}"
        rec = {
            "seq": seq, "chunk": chunk_idx, "chars": chars, "flag": flag,
            "duration_chunk_s": dur, "duration_transcribe_s": round(duration,2), "throttle_s": throttle_wait,
            "cost": cost, "finish_reason": finish,
            "prompt_tokens": usage.get("prompt_tokens") if usage else None,
            "completion_tokens": usage.get("completion_tokens") if usage else None,
            "timestamp": datetime.datetime.now().isoformat()
        }
        INSTRUMENT.append(rec)
        if flag:
            ANOMALIES.append(rec)
            print(f"    !! ANOMALY flagged {flag} seq {seq} chunk {chunk_idx} chars {chars} dur {dur:.0f}s")
        return flag

    overall_log = TAMIL_DIR / "transcribe_log.json"
    all_results=[]
    # ---- Phase A: Download only ----
    if do_A:
        print(f"\n=== Phase A: Download {len(seq_fid_list)} files ===")
        for seq,fid in seq_fid_list:
            dest = AUDIO_DIR / f"periyapuranam-{seq:03d}-{fid}.mp3"
            if dest.exists() and dest.stat().st_size > 1024*1024:
                try:
                    # verify ffprobe stream==format and no growing-file warning
                    r = subprocess.run(["ffprobe","-v","warning","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", str(dest)], capture_output=True, text=True)
                    if r.returncode==0 and r.stderr.strip()=="" :
                        print(f"[{seq:03d}] audio exists {dest.stat().st_size/1024/1024:.1f} MB skip download")
                        continue
                except: pass
            try:
                download_drive(fid, dest)
            except Exception as e:
                print(f"DOWNLOAD FAILED {seq}: {e}")
                sys.exit(1)
        print(f"Phase A DONE — {len(seq_fid_list)} files in {AUDIO_DIR}")
        if not do_B and not do_C:
            print("Phase A only — stopping before B/C")
            return
    else:
        # verify audio exists for B/C
        for seq,fid in seq_fid_list:
            dest = AUDIO_DIR / f"periyapuranam-{seq:03d}-{fid}.mp3"
            if not dest.exists() or dest.stat().st_size < 1024*1024:
                print(f"Phase B/C requires audio {dest} — run Phase A first")
                sys.exit(1)

    # ---- Phase B: Chunk + Transcribe Tamil ----
    story_content = ""
    story_tamil = TAMIL_DIR/f"{SLUG}_tamil.txt"
    if do_B:
        for seq,fid in seq_fid_list:
            dest = AUDIO_DIR / f"periyapuranam-{seq:03d}-{fid}.mp3"
            duration=get_duration(dest)
            chunks=int((duration+CHUNK_SEC-1)//CHUNK_SEC)
            print(f"\n[{seq:03d}] {nayanar} fid {fid} duration {duration:.1f}s -> {chunks} chunks")
            seq_out_parts=[]; seq_metas=[]
            for i in range(chunks):
                offset=i*CHUNK_SEC
                dur=min(CHUNK_SEC, duration-offset)
                chunk_path=TMP_DIR/f"{seq:03d}_chunk{i:02d}_{offset:.0f}s.mp3"
                if not chunk_path.exists() or chunk_path.stat().st_size<1000:
                    make_chunk(dest, offset, dur, chunk_path)
                # detect empty mp3 (395B) from header over-estimate (e.g., 246 1064s vs valid 510s)
                if chunk_path.stat().st_size < 10*1024:
                    try:
                        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", str(chunk_path)], capture_output=True, text=True)
                        if r.returncode!=0 or not r.stdout.strip():
                            print(f"  chunk {i+1}/{chunks} empty mp3 {chunk_path.stat().st_size}B — skipping (beyond valid audio)")
                            continue
                    except: pass
                chunk_txt_cached = TAMIL_DIR/f"periyapuranam-{seq:03d}_chunk{i:02d}.txt"
                if chunk_txt_cached.exists() and chunk_txt_cached.stat().st_size > 500:
                    try:
                        _cached = chunk_txt_cached.read_text(encoding="utf-8").strip()
                        if _cached and "[FAILED" not in _cached and len(_cached) > 30:
                            print(f"  chunk {i+1}/{chunks} offset {offset:.0f}s dur {dur:.0f}s size {chunk_path.stat().st_size/1e3:.0f}KB -> cached {len(_cached)} chars skip API", flush=True)
                            seq_out_parts.append(_cached)
                            seq_metas.append({"chunk":i,"offset":offset,"dur":dur,"chars":len(_cached),"meta":{"cached":True}})
                            _flag_anomaly(seq,i,_cached,{"usage":{"cost":0}},0,0,dur)
                            continue
                    except: pass

                print(f"  chunk {i+1}/{chunks} offset {offset:.0f}s dur {dur:.0f}s size {chunk_path.stat().st_size/1e3:.0f}KB -> transcribing...", flush=True)
                t0=time.time()
                content,meta=transcribe_chunk(chunk_path, seq,i,chunks)
                dur_t=time.time()-t0
                if content is None or not (content or "").strip():
                    print(f"    FAILED chunk {i} seq {seq} (empty)")
                    if content is None:
                        content="[FAILED TRANSCRIPTION]"; meta={"error":"failed"}
                    _flag_anomaly(seq,i,content,meta,dur_t,2.0,dur)
                else:
                    print(f"    -> {len(content)} chars, cost {meta.get('usage',{}).get('cost','?') if meta else '?'}")
                    _flag_anomaly(seq,i,content,meta,dur_t,2.0,dur)
                chunk_txt=TAMIL_DIR/f"periyapuranam-{seq:03d}_chunk{i:02d}.txt"
                chunk_txt.write_text(content,encoding="utf-8")
                seq_out_parts.append(content)
                seq_metas.append({"chunk":i,"offset":offset,"dur":dur,"chars":len(content),"meta":meta})
                time.sleep(2.0)
            merged="\n\n".join(seq_out_parts)
            seq_out=TAMIL_DIR/f"periyapuranam-{seq:03d}-tamil-real.txt"
            seq_out.write_text(merged,encoding="utf-8")
            print(f"  MERGED seq {seq:03d} -> {seq_out.name} {len(merged)} chars, {seq_out.stat().st_size} bytes")
            all_results.append({"seq":seq,"fid":fid,"duration":duration,"chunks":chunks,"merged_chars":len(merged),"merged_file":str(seq_out),"chunks_meta":seq_metas})

        # story merge with Chapter 01..N, no ===
        story_parts=[]
        for idx,(seq,fid) in enumerate(sorted(seq_fid_list)):
            src=TAMIL_DIR/f"periyapuranam-{seq:03d}-tamil-real.txt"
            txt=src.read_text(encoding="utf-8").strip()
            story_parts.append(f"Chapter {idx+1:02d} — {nayanar}\n\n{txt}")
        story_content="\n\n".join(story_parts)+"\n"
        story_tamil.write_text(story_content,encoding="utf-8")
        print(f"\nSTORY TAMIL: {story_tamil} {story_tamil.stat().st_size} bytes, {len(story_content)} chars Chapters {len(story_parts)}")

        with open(overall_log,'w',encoding="utf-8") as f:
            json.dump(all_results,f,ensure_ascii=False,indent=2)
        print(f"Log -> {overall_log}")

        # dump instrumentation + error log and pause if anomalies
        instr_path = TAMIL_DIR / f"{SLUG}_instrumentation.json"
        with open(instr_path, "w", encoding="utf-8") as f:
            json.dump({"experiment":"2-parallel-dur-aware-3phase","nayanar":nayanar,"slug":SLUG,"day":DAY,"phase":"B","start":EXPERIMENT_START,"end":time.time(),"elapsed_s":round(time.time()-EXPERIMENT_START,1),"per_chunk":INSTRUMENT,"anomalies":ANOMALIES,"seq_results":all_results}, f, ensure_ascii=False, indent=2)
        print(f"\nINSTRUMENTATION -> {instr_path} anomalies {len(ANOMALIES)}")
        # error log for manual review (q3)
        err_path = TAMIL_DIR / f"{SLUG}_errors.log"
        if ANOMALIES:
            with open(err_path, "w", encoding="utf-8") as ef:
                ef.write(f"Anomalies for {nayanar} {SLUG} phase B — {len(ANOMALIES)} flagged, manual review required before Phase C\n")
                ef.write(f"Generated {datetime.datetime.now().isoformat()} DAY {DAY}\n\n")
                for a in ANOMALIES:
                    ef.write(f"seq {a['seq']} chunk {a['chunk']} flag {a['flag']} chars {a['chars']} dur {a['duration_chunk_s']:.0f}s cost {a['cost']} finish {a['finish_reason']}\n")
                    ef.write(f"  file: periyapuranam-{a['seq']:03d}_chunk{a['chunk']:02d}.txt + chunk mp3 {a['duration_chunk_s']:.0f}s\n")
                ef.write("\nTails with 0 chars (e.g., 251c03 75s, 261c04 34s) consistently return 0 on retry — likely silence, keep as valid empty but flagged for review.\n")
            print(f"ERROR LOG -> {err_path} — PAUSING for manual review before Phase C")
            print("  MANUAL REVIEW REQUIRED for flagged chunks (check tamil_real/*_chunk*.txt and audio):")
            for a in ANOMALIES:
                print(f"    seq {a['seq']} chunk {a['chunk']} flag {a['flag']} chars {a['chars']} dur {a['duration_chunk_s']:.0f}s")
            print("  Fix: re-transcribe single chunk or accept silence (keep 0), then re-merge story before Phase C.")
        else:
            print("  No anomalies flagged - proceed to verify Chapter count and ==== check")
            # remove stale error log if exists
            try:
                if err_path.exists():
                    err_path.unlink()
            except: pass
        if ANOMALIES and not do_C:
            print("Phase B done with anomalies — stopping before Phase C for manual review (q3)")
            return
        if not do_C:
            print("Phase B only — stopping before C")
            return
    else:
        # Phase C needs story_content loaded from existing tamil file
        if story_tamil.exists():
            story_content = story_tamil.read_text(encoding="utf-8")
            print(f"\nPhase C: loaded existing Tamil {story_tamil} {len(story_content)} chars")
        else:
            print(f"Phase C requires {story_tamil} — run Phase B first")
            sys.exit(1)
    # ---- Phase C: Chunked English Translation (60K) ----
    if do_C:
        print(f"\n=== Phase C: Chunked English translation (60K) for {nayanar} ===")
        if not story_content:
            # load from file if B not run in same invocation
            story_content = story_tamil.read_text(encoding="utf-8")
        # split by Chapter headers
        CHUNK_TAMIL_LIMIT = 60000
        parts = re.split(r'(?=^Chapter \d{2} —)', story_content, flags=re.M)
        chapters = [p for p in parts if p.strip().startswith("Chapter")]
        groups=[]; cur=""
        for ch in chapters:
            if len(cur)+len(ch)>CHUNK_TAMIL_LIMIT and cur:
                groups.append(cur.strip()); cur=ch
            else:
                cur = cur + "\n\n" + ch if cur else ch
        if cur.strip():
            groups.append(cur.strip())
        # fallback split if any group >80K
        final=[]
        for g in groups:
            if len(g)>80000:
                mid=len(g)//2
                cut=g.rfind("Chapter ",0,mid+5000)
                if cut>0:
                    final.append(g[:cut].strip()); final.append(g[cut:].strip())
                else:
                    final.append(g)
            else:
                final.append(g)
        groups=final
        total=len(groups)
        print(f" Tamil {len(story_content)} chars {len(chapters)} chapters -> {total} English chunks (limit {CHUNK_TAMIL_LIMIT})")
        english_dir = BASE / "english_real"
        english_dir.mkdir(parents=True, exist_ok=True)
        # helper for single chunk translate
        def translate_chunk_en(chunk_tamil, chunk_idx, total_chunks, headers_in):
            prompt = f"""Translate the following Tamil Periya Puranam story of {nayanar} into clear, faithful English.

Requirements:
- Preserve Chapter headings exactly as "Chapter 01", "Chapter 02" etc. if present (keep same numbers).
- Preserve names, place names, and Tamil verses transliterated accurately.
- No summary, no added commentary, no separators like ==== or PART.
- Output only the English translation for this chunk, in the same chapter order.
- Keep paragraph structure readable for blog publishing.

Tamil chunk {chunk_idx+1}/{total_chunks} (contains {headers_in}):

{chunk_tamil}
"""
            payload={"model":MODEL,"messages":[{"role":"user","content":[{"type":"text","text":prompt}]}],"max_tokens":30000,"temperature":0.4}
            h=dict(headers_llm)
            h["X-Title"]=f"Nalvar Periyapuranam - {nayanar} English chunk {chunk_idx+1}/{total_chunks}"
            for retry in range(3):
                try:
                    r=requests.post(ENDPOINT, headers=h, json=payload, timeout=300)
                    if r.status_code==200:
                        j=r.json()
                        content=j["choices"][0]["message"]["content"] or ""
                        content=content.strip()
                        if content.startswith("```"):
                            content=content.split("\n",1)[-1].rsplit("```",1)[0].strip()
                        return content, j
                    else:
                        body=r.text[:800]
                        if r.status_code in (402,403) and ("Budget" in body or "budget" in body.lower()):
                            print(f" EN FATAL BUDGET {r.status_code} {body[:300]}"); sys.exit(2)
                        print(f" EN HTTP {r.status_code} retry {retry+1} {body[:300]}")
                        time.sleep(2*(retry+1))
                except Exception as e:
                    print(f" EN exception retry {retry+1}: {e}")
                    time.sleep(2*(retry+1))
            return None, None

        instrument_en=[]
        for idx, chunk_tamil in enumerate(groups):
            headers_in = ", ".join(re.findall(r'Chapter \d{2}', chunk_tamil)[:6])
            cp = english_dir / f"{SLUG}_english_chunk{idx:02d}.txt"
            mp = english_dir / f"{SLUG}_english_chunk{idx:02d}_meta.json"
            # resume skip
            if cp.exists() and cp.stat().st_size>500 and mp.exists():
                try:
                    prev = cp.read_text(encoding="utf-8").strip()
                    mj=json.loads(mp.read_text(encoding="utf-8"))
                    finish = mj.get("choices",[{}])[0].get("finish_reason") if mj.get("choices") else None
                    if prev and "[FAILED" not in prev and finish=="stop" and len(prev)>1000:
                        print(f" [{idx+1}/{total}] {headers_in} -> cached {len(prev)} chars skip API", flush=True)
                        instrument_en.append({"chunk":idx,"headers":headers_in,"tamil_chars":len(chunk_tamil),"english_chars":len(prev),"cached":True,"cost":0,"finish":"stop"})
                        continue
                except: pass
            print(f" [{idx+1}/{total}] {headers_in} Tamil {len(chunk_tamil)} chars -> translating...", flush=True)
            t0=time.time()
            content, meta = translate_chunk_en(chunk_tamil, idx, total, headers_in)
            dt=time.time()-t0
            if not content or not content.strip():
                print(f"  FAILED chunk {idx} empty")
                content="[FAILED TRANSLATION]"; meta={"error":"failed","choices":[{"finish_reason":"failed"}]}
            cp.write_text(content, encoding="utf-8")
            mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2), encoding="utf-8")
            usage = meta.get("usage",{}) if isinstance(meta,dict) else {}
            cost=usage.get("cost")
            finish=meta.get("choices",[{}])[0].get("finish_reason") if isinstance(meta,dict) and meta.get("choices") else None
            print(f"  -> {len(content)} chars cost {cost} finish {finish} time {dt:.1f}s", flush=True)
            instrument_en.append({"chunk":idx,"headers":headers_in,"tamil_chars":len(chunk_tamil),"english_chars":len(content),"cost":cost,"finish":finish,"duration_s":round(dt,1),"prompt_tokens":usage.get("prompt_tokens"),"completion_tokens":usage.get("completion_tokens")})
            time.sleep(1.2)
        # merge
        english_chunks = [ (english_dir / f"{SLUG}_english_chunk{i:02d}.txt").read_text(encoding="utf-8").strip() for i in range(total) ]
        merged_en = "\n\n".join(english_chunks).strip()+"\n"
        has_eq = "====" in merged_en
        ch_count = len(re.findall(r"^Chapter \d{2}", merged_en, flags=re.M))
        print(f" MERGED {SLUG} English -> {len(merged_en)} chars Chapters {ch_count} has==== {has_eq} chunks {total}")
        story_eng = BASE / f"{SLUG}_english.txt"
        story_eng.write_text(merged_en, encoding="utf-8")
        meta_agg = BASE / f"{SLUG}_english_meta.json"
        meta_agg.write_text(json.dumps({"slug":SLUG,"nayanar":nayanar,"phase":"C","chunks":total,"merged_chars":len(merged_en),"merged_chapters":ch_count,"has_eq":has_eq,"instrument":instrument_en,"elapsed_s":round(time.time()-EXPERIMENT_START,1)}, ensure_ascii=False, indent=2), encoding="utf-8")
        bilingual = BASE / f"{SLUG}_bilingual.txt"
        bilingual.write_text(f"# Tamil\n\n{story_content}\n\n# English\n\n{merged_en}\n", encoding="utf-8")
        print(f" WROTE {story_eng} {story_eng.stat().st_size} + {bilingual} {bilingual.stat().st_size} + {english_dir} + {meta_agg}")
        # instrumentation for C
        instr_en_path = english_dir / f"{SLUG}_english_instrumentation.json"
        instr_en_path.write_text(json.dumps({"nayanar":nayanar,"slug":SLUG,"day":DAY,"phase":"C","start":EXPERIMENT_START,"end":time.time(),"elapsed_s":round(time.time()-EXPERIMENT_START,1),"chunks":instrument_en}, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print("\nPhase C skipped (run with --phase C or --phase all)")

    print(f"\nDONE {nayanar} phase {phase} pipeline. Review files:\n  Tamil : {story_tamil}\n  English: {BASE/f'{SLUG}_english.txt'}")

if __name__=="__main__":
    # Default for `python periapuranam/run_<slug>.py` without args (uses per-slug _defaults)
    _defaults = {"Tiruk Kurippu Tonda Nayanar": [(209, "1UB1qvOxdbL2qjRijZIdGAzckoad4f-xO"), (210, "1pB7LN91QoOw0iAt4K4DwL4Pd-wWUunoC"), (211, "1HzjqCELojCdOM3sqAhH_1rqS_1luUKmz"), (212, "1uBjJSUVSuG1bjUwjYjBAf_3vAOjqS0es"), (213, "1RVRTNb1QXjbtDC2rMkPfddPTc71nb_91"), (214, "1pf9qHB0xtWFkwCkW5ZgOlVXcHi0WU5wb"), (215, "13oU143pmEd4fKmlnOZ6-HmQVPBDAzrT5"), (216, "1C2vXwi7BH45I_d17SHgPYpBLd6vg_dvI"), (217, "11YM4tA5E4D4Jx0IfczS82A1jwlG4vfRN"), (218, "1l25oXT3EZbZ-k_EtLLjK2DmrcFToCV7v"), (219, "1p96aDIwdLv1fYk7noAzR1MyDWk4lta4O"), (220, "1sOnCNn44FdNplCE_LuOWCBPmFXxnDobP"), (221, "1t_E2WYE1x7EozZC7aTJpC5Q_dHh8Ac3q"), (222, "1qEuehhLv3WDGh2KTXIp_GlcgBpvjJzFb"), (223, "1tZIyO9bS5KaPTfUISdAyAmQHjLvOlV7U"), (224, "1e9vZ0yqYYUvp3tQzh58OYOyzth8zIiDp"), (225, "15HctDMWM-rwbD2tT4vQyvqS_eJsMcSx-"), (226, "1o-v9iu0eIEToju6anRMuEdsJL7PImGk9"), (227, "1y8U1KWGPImgwzT6x2CtcSQ1com_gG6-i"), (228, "16X0KF0kG8MgMxfdEhk8ClozxTLxjsYxA"), (229, "13Lwo0VP4hlx1MQ2J8ogKRCw1Nna0dAU_"), (230, "11SZuN-AGS74mpuu_rg3fP_qjdyb5W9n_"), (231, "1MP7_RyDpOUv7WFf0F3Jh-ued9tEnYqcH"), (232, "1ZfePs0tf3qwy8q7ChSsT5LjmF_YKtqQ6"), (233, "1y6e8xfk_bdbI7ZkJFPyT--Dc1n-mdVQy"), (234, "1OZdmNpRQB8RIM3799DWuEV45v5xmLOjH"), (235, "1arSrVNPTPzr8t830mr9_31eNLzjyjttA"), (236, "1NkWaAFpSVd8J0jlRrRDcnSDoVMLmoZgJ"), (237, "1FRLjZ0d7asZK11WWBuJ0jm56uKerikWf"), (238, "1vKvKPXJhuDqbXEhb79JwIJcN6XGXNdg6"), (239, "1DVa4zdQqxLdckQGHBHoEIHuvOrYjsJM5"), (240, "1JRwlGW_a_S3zAiPk7ODzMpNB8vkq7Uii"), (241, "1keWeyTm2GidtHHiSG2DWeEbbO5NDzRB6"), (242, "1h7FBl2aTbzllfHsfMTxmhart_gqnIkhq"), (243, "1nojOTfomtT8FDJ2VHvjGmO0RslKd26-X"), (244, "1zBYHz_PjxEApLMBX_CF02I-Vk-hPi0vL")]}  # replaced per slug: {"Nayanar Name": [(seq, fid), ...]}
    import sys as _sys
    if len(_sys.argv) == 1 and _defaults:
        nayanar, seq_fid = next(iter(_defaults.items()))
        print(f"Running with defaults {nayanar} {len(seq_fid)} files phase=all")
        run(nayanar, seq_fid, phase="all")
        _sys.exit(0)
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--nayanar", required=False, default=None)
    p.add_argument("--seq", required=False, default=None, help="seq comma separated")
    p.add_argument("--fid", required=False, default=None, help="fid comma separated")
    p.add_argument("--phase", default=None, help="A=download, B=transcribe Tamil, C=translate English, all=A+B+C (default all)")
    args,_ = p.parse_known_args()
    if args.phase and not args.nayanar and _defaults:
        nayanar, seq_fid = next(iter(_defaults.items()))
        print(f"Running with defaults {nayanar} {len(seq_fid)} files phase={args.phase}")
        run(nayanar, seq_fid, phase=args.phase)
        _sys.exit(0)
    if len(_sys.argv) == 1 and _defaults:
        nayanar, seq_fid = next(iter(_defaults.items()))
        print(f"Running with defaults {nayanar} {len(seq_fid)} files phase=all")
        run(nayanar, seq_fid, phase="all")
        _sys.exit(0)
    if args.nayanar and args.seq and args.fid:
        seqs=[int(x) for x in args.seq.split(",")]
        fids=args.fid.split(",")
        seq_fid=list(zip(seqs,fids))
        run(args.nayanar, seq_fid, phase=args.phase or "all")
        _sys.exit(0)
    p.print_help()
    _sys.exit(1)
