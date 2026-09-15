#!/usr/bin/env python3
import pathlib, subprocess, base64, requests, os, json, time, sys, datetime, collections
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "google/gemini-2.5-flash"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
CHUNK_SEC = 300

def slugify(name):
    return name.lower().replace(" ","_").replace("(","").replace(")","").replace("-","_").replace("__","_").strip("_")

def run(nayanar, seq_fid_list):
    SLUG = slugify(nayanar)
    DAY = "day-04"  # change per batch: day-01, day-02, ... day-10, day-11+
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
        print(f"  DOWNLOAD {file_id} -> {dest.name} ...")
        session = requests.Session()
        resp = session.get(url, headers=headers_dl, stream=True, timeout=60)
        token = None
        for k,v in resp.cookies.items():
            if k.startswith("download_warning"):
                token = v
                break
        if token:
            params = {"id": file_id, "export": "download", "confirm": token}
            resp = session.get("https://drive.usercontent.google.com/download", params=params, headers=headers_dl, stream=True, timeout=60)
        resp.raise_for_status()
        total=0
        with open(dest,"wb") as f:
            for chunk in resp.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
                    total+=len(chunk)
        print(f"    -> {total/1024/1024:.1f} MB")
        return total
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
                    print(f"    HTTP {r.status_code} retry {retry+1}: {r.text[:400]}")
                    time.sleep(2*(retry+1))
            except Exception as e:
                print(f"    exception retry {retry+1}: {e}")
                time.sleep(2*(retry+1))
        
    # === INSTRUMENTATION & FAIL-SAFE (parallel experiment 2-workers) ===
    INSTRUMENT = []  # per-chunk
    ANOMALIES = []
    EXPERIMENT_START = time.time()
    def _flag_anomaly(seq, chunk_idx, content, meta, duration, throttle_wait):
        chars = len(content) if content else 0
        flag = None
        if chars == 0:
            flag = "EMPTY_0CHAR"
        elif chars < 500:
            flag = f"TINY_{chars}"
        elif chars > 8000:
            flag = f"HUGE_{chars}"
        else:
            if chars > 1000:
                from collections import Counter
                windows = [content[i:i+8] for i in range(0, len(content)-8, 8)]
                if windows:
                    most_common, cnt = Counter(windows).most_common(1)[0]
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
        if finish and finish != "stop":
            flag = (flag + "|" if flag else "") + f"FINISH_{finish}"
        rec = {
            "seq": seq, "chunk": chunk_idx, "chars": chars, "flag": flag,
            "duration_s": round(duration,2), "throttle_s": throttle_wait,
            "cost": cost, "finish_reason": finish,
            "prompt_tokens": usage.get("prompt_tokens") if usage else None,
            "completion_tokens": usage.get("completion_tokens") if usage else None,
            "timestamp": datetime.datetime.now().isoformat()
        }
        INSTRUMENT.append(rec)
        if flag:
            ANOMALIES.append(rec)
            print(f"    !! ANOMALY flagged {flag} seq {seq} chunk {chunk_idx} chars {chars}")
        return flag

    overall_log = TAMIL_DIR / "transcribe_log.json"
    all_results=[]
    for seq,fid in seq_fid_list:
        dest = AUDIO_DIR / f"periyapuranam-{seq:03d}-{fid}.mp3"
        if not dest.exists() or dest.stat().st_size < 1024*1024:
            try:
                download_drive(fid, dest)
            except Exception as e:
                print(f"DOWNLOAD FAILED {seq}: {e}")
                sys.exit(1)
        else:
            print(f"[{seq:03d}] audio exists {dest.stat().st_size/1024/1024:.1f} MB skip download")
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
            print(f"  chunk {i+1}/{chunks} offset {offset:.0f}s dur {dur:.0f}s size {chunk_path.stat().st_size/1e3:.0f}KB -> transcribing...")
            t0=time.time()
            content,meta=transcribe_chunk(chunk_path, seq,i,chunks)
            dur_t=time.time()-t0
            if content is None:
                print(f"    FAILED chunk {i} seq {seq}")
                content="[FAILED TRANSCRIPTION]"; meta={"error":"failed"}
                _flag_anomaly(seq,i,content,meta,dur_t,1.2)
            else:
                print(f"    -> {len(content)} chars, cost {meta.get('usage',{}).get('cost','?') if meta else '?'}")
                _flag_anomaly(seq,i,content,meta,dur_t,1.2)
            chunk_txt=TAMIL_DIR/f"periyapuranam-{seq:03d}_chunk{i:02d}.txt"
            chunk_txt.write_text(content,encoding="utf-8")
            seq_out_parts.append(content)
            seq_metas.append({"chunk":i,"offset":offset,"dur":dur,"chars":len(content),"meta":meta})
            time.sleep(1.2)
        merged="\n\n".join(seq_out_parts)
        seq_out=TAMIL_DIR/f"periyapuranam-{seq:03d}-tamil-real.txt"
        seq_out.write_text(merged,encoding="utf-8")
        print(f"  MERGED seq {seq:03d} -> {seq_out.name} {len(merged)} chars, {seq_out.stat().st_size} bytes")
        all_results.append({"seq":seq,"fid":fid,"duration":duration,"chunks":chunks,"merged_chars":len(merged),"merged_file":str(seq_out),"chunks_meta":seq_metas})

    # story merge with Chapter 01..N, no ===
    story_tamil=TAMIL_DIR/f"{SLUG}_tamil.txt"
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

    # translation
    # dump instrumentation before translate
    instr_path = TAMIL_DIR / f"{SLUG}_instrumentation.json"
    with open(instr_path, "w", encoding="utf-8") as f:
        json.dump({"experiment":"2-workers-parallel","nayanar":nayanar,"slug":SLUG,"day":DAY,"start":EXPERIMENT_START,"end":time.time(),"elapsed_s":round(time.time()-EXPERIMENT_START,1),"per_chunk":INSTRUMENT,"anomalies":ANOMALIES,"seq_results":all_results}, f, ensure_ascii=False, indent=2)
    print(f"\nINSTRUMENTATION -> {instr_path} anomalies {len(ANOMALIES)}")
    if ANOMALIES:
        print("  MANUAL REVIEW REQUIRED for flagged chunks (check tamil_real/*_chunk*.txt and audio):")
        for a in ANOMALIES:
            print(f"    seq {a['seq']} chunk {a['chunk']} flag {a['flag']} chars {a['chars']}")
    else:
        print("  No anomalies flagged - proceed to verify Chapter count and ==== check")
    print("\nTranslating to English (single call)...")
    translate_prompt=f"""Translate the following Tamil Periya Puranam story of {nayanar} into clear, faithful English.

Requirements:
- Preserve Chapter headings exactly as \"Chapter 01\", \"Chapter 02\" etc. if present.
- Preserve names, place names, and Tamil verses transliterated accurately.
- No summary, no added commentary, no separators like ==== or PART.
- Output only the English translation, in the same chapter order.
- Keep paragraph structure readable for blog publishing.

Tamil source:
{story_content}
"""
    headers_en=dict(headers_llm)
    headers_en["X-Title"]=f"Nalvar Periyapuranam - {nayanar} English"
    payload_en={"model":MODEL,"messages":[{"role":"user","content":[{"type":"text","text":translate_prompt}]}],"max_tokens":30000,"temperature":0.4}
    for retry in range(3):
        try:
            r=requests.post(ENDPOINT, headers=headers_en, json=payload_en, timeout=300)
            if r.status_code==200:
                j=r.json()
                eng=j["choices"][0]["message"]["content"] or ""
                eng=eng.strip()
                if eng.startswith("```"):
                    eng=eng.split("\n",1)[-1].rsplit("```",1)[0].strip()
                story_eng=BASE/f"{SLUG}_english.txt"
                story_eng.write_text(eng,encoding="utf-8")
                meta_en=BASE/f"{SLUG}_english_meta.json"
                meta_en.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding="utf-8")
                print(f"ENGLISH -> {story_eng} {len(eng)} chars, cost {j.get('usage',{}).get('cost','?')}")
                bilingual=BASE/f"{SLUG}_bilingual.txt"
                bilingual.write_text(f"# Tamil\n\n{story_content}\n\n# English\n\n{eng}\n",encoding="utf-8")
                print(f"BILINGUAL -> {bilingual}")
                break
            else:
                print(f"EN HTTP {r.status_code}: {r.text[:500]}")
                time.sleep(2*(retry+1))
        except Exception as e:
            print(f"EN exception {e}")
            time.sleep(2*(retry+1))
    else:
        print("EN TRANSLATION FAILED")
    print(f"\nDONE {nayanar} pipeline. Review files:\n  Tamil : {story_tamil}\n  English: {BASE/f'{SLUG}_english.txt'}")

if __name__=="__main__":
    # parallel experiment defaults (instrumented) - no-args fallback
    _defaults = {
        "Mei-p-porul Nayanar": [(78, '1jabkJh2ZhF_u1CeHfvHOShkafdm1bpZS'), (79, '1iDDAo6CdKtW0D5DNdvBWvhsu8TgirYQn'), (80, '1PloBX2YrBakxpe2B3xgrvC7fe8A2ybXz'), (81, '1ro8knoXsmaK5cD8Kx_RnBKMcG3sfNsvE'), (82, '19Zp0-klSELzorZd1x6y1t8vnjqE4BvC5'), (83, '1Xn6jv-gall6b_uIEVL5rujF7Zetr9HVJ'), (84, '1ZscDQrKyGOL6L3KNg_wjCBv4uGbAxmLs')],
        "Sakkiya Nayanar": [(915, '15MfnAlHBTFdHUTnqU_Ixl11eo_9yXsGo'), (916, '1gwO_8WfBdkEaJqfpWsL6wAVUSHDLn8uB'), (917, '1WxxOMXyS42L6DAIhK3u9ZM9ptJQWilZu'), (918, '1Kc6S7ruGyNcX-VZTtWTnuV0SKkCF13j3'), (919, '1a1nrLMG5qdEHE6AWh28AuZY0pYTyEdL4'), (920, '19a_RStdRD0ZYZkFHZP5POmrw4yprXdL8'), (921, '1IPSBgK8tsX-k0zwlTToMOJ70kicMVzed'), (922, '1QdTktNepjaZsbPt7WXCqvztv8r8HBRvu')],
    }
    if len(sys.argv) == 1:
        import pathlib as _pl
        stem = _pl.Path(__file__).stem
        if "mei_p_porul" in stem:
            run("Mei-p-porul Nayanar", _defaults["Mei-p-porul Nayanar"])
        elif "sakkiya" in stem:
            run("Sakkiya Nayanar", _defaults["Sakkiya Nayanar"])
        else:
            print("No args and unknown default - provide --nayanar and --seq/--fid")
        sys.exit(0)
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--nayanar", required=True)
    p.add_argument("--seq", required=True, help="seq comma separated")
    p.add_argument("--fid", required=True, help="fid comma separated")
    args=p.parse_args()
    seqs=[int(x) for x in args.seq.split(",")]
    fids=args.fid.split(",")
    seq_fid=list(zip(seqs,fids))
    run(args.nayanar, seq_fid)
