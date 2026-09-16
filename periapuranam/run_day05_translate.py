#!/usr/bin/env python3
"""
Pass 2 — Chunked English translation (separate callable, not batched in transcribe).
Tamil already verified (Day05 13-file stories). Translates each story's
tamil_real/<slug>_tamil.txt in 2-3 chapter-group chunks, stores
english_real/<slug>_english_chunk*.txt + instrumentation, merges to
<slug>_english.txt + bilingual. Progress by event + 5-min heartbeat.
"""
import pathlib, os, json, requests, time, sys, re, datetime

API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "google/gemini-2.5-flash"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
ROOT = pathlib.Path(__file__).parent
DAY = "day-05"
SLUGS = [
    ("amar_niti_nayanar","Amar-Niti Nayanar"),
    ("eri_pattha_nayanar","Eri-Pattha Nayanar"),
    ("siruthonda_nayanar","Siruthonda Nayanar"),
]
# chunk Tamil by chapters: accumulate until >60k chars then cut (keeps each <15K tokens completion)
CHUNK_TAMIL_LIMIT = 60000
HEARTBEAT_S = 300

def chunk_tamil_by_chapters(story_text):
    # split on "Chapter 01 —" headers (keep delimiter)
    parts = re.split(r'(?=^Chapter \d{2} —)', story_text, flags=re.M)
    # parts may include leading empty; filter
    chapters = [p for p in parts if p.strip().startswith("Chapter")]
    # group
    groups=[]; cur=""; cur_headers=[]
    for ch in chapters:
        if len(cur) + len(ch) > CHUNK_TAMIL_LIMIT and cur:
            groups.append(cur.strip())
            cur=ch
        else:
            cur = cur + "\n\n" + ch if cur else ch
    if cur.strip():
        groups.append(cur.strip())
    # if single huge chunk still >80k, split mid (fallback)
    final=[]
    for g in groups:
        if len(g) > 80000:
            mid=len(g)//2
            # try split at chapter boundary near mid
            cut=g.rfind("Chapter ", 0, mid+5000)
            if cut>0:
                final.append(g[:cut].strip()); final.append(g[cut:].strip())
            else:
                final.append(g)
        else:
            final.append(g)
    return final, chapters

def translate_chunk(chunk_tamil, nayanar, chunk_idx, total_chunks, chapter_headers):
    prompt = f"""Translate the following Tamil Periya Puranam story of {nayanar} into clear, faithful English.

Requirements:
- Preserve Chapter headings exactly as "Chapter 01", "Chapter 02" etc. if present (keep same numbers).
- Preserve names, place names, and Tamil verses transliterated accurately.
- No summary, no added commentary, no separators like ==== or PART.
- Output only the English translation for this chunk, in the same chapter order.
- Keep paragraph structure readable for blog publishing.

Tamil chunk {chunk_idx+1}/{total_chunks} (contains {chapter_headers}):

{chunk_tamil}
"""
    payload={"model":MODEL,"messages":[{"role":"user","content":[{"type":"text","text":prompt}]}],"max_tokens":30000,"temperature":0.4}
    headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json","HTTP-Referer":"https://nalvar.in","X-Title":f"Nalvar Periyapuranam - {nayanar} English chunk {chunk_idx+1}/{total_chunks}"}
    for retry in range(3):
        try:
            r=requests.post(ENDPOINT, headers=headers, json=payload, timeout=300)
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
                    print(f" FATAL BUDGET {r.status_code} {body[:300]}"); sys.exit(2)
                print(f" HTTP {r.status_code} retry {retry+1} {body[:300]}")
                time.sleep(2*(retry+1))
        except Exception as e:
            print(f" exception retry {retry+1}: {e}")
            time.sleep(2*(retry+1))
    return None, None

def run_slug(slug, nayanar):
    base = ROOT / "output" / DAY / slug
    tamil_path = base / "tamil_real" / f"{slug}_tamil.txt"
    english_dir = base / "english_real"
    english_dir.mkdir(parents=True, exist_ok=True)
    story_tamil = tamil_path.read_text(encoding="utf-8")
    groups, all_chapters = chunk_tamil_by_chapters(story_tamil)
    total = len(groups)
    print(f"\n=== TRANSLATE {nayanar} -> {slug} Tamil {len(story_tamil)} chars {len(all_chapters)} chapters -> {total} English chunks (limit {CHUNK_TAMIL_LIMIT}) ===")
    # clean old english_real chunks for idempotent rerun
    # keep if exists and >500 and not failed? But we re-translate fresh; remove old to avoid stale
    for old in english_dir.glob(f"{slug}_english_chunk*.txt"):
        # will overwrite
        pass

    instrument=[]
    anomalies=[]
    t_start=time.time()
    english_chunks=[]

    for idx, chunk_tamil in enumerate(groups):
        # extract chapter headers in this chunk for prompt
        headers_in_chunk = ", ".join(re.findall(r'Chapter \d{2}', chunk_tamil)[:6])
        chunk_path = english_dir / f"{slug}_english_chunk{idx:02d}.txt"
        meta_path = english_dir / f"{slug}_english_chunk{idx:02d}_meta.json"
        # idempotent resume: if chunk exists >500 and not truncated and meta finish=stop, skip
        if chunk_path.exists() and chunk_path.stat().st_size>500 and meta_path.exists():
            try:
                prev = chunk_path.read_text(encoding="utf-8").strip()
                mj=json.loads(meta_path.read_text(encoding="utf-8"))
                finish = mj.get("choices",[{}])[0].get("finish_reason") if mj.get("choices") else None
                if prev and "[FAILED" not in prev and finish=="stop" and len(prev)>1000:
                    print(f" [{idx+1}/{total}] {headers_in_chunk} -> cached {len(prev)} chars skip API", flush=True)
                    english_chunks.append(prev)
                    # instrument cached
                    instrument.append({"chunk":idx,"headers":headers_in_chunk,"tamil_chars":len(chunk_tamil),"english_chars":len(prev),"cached":True,"cost":0,"finish":"stop","duration_s":0})
                    continue
            except: pass
        print(f" [{idx+1}/{total}] {headers_in_chunk} Tamil {len(chunk_tamil)} chars -> translating...", flush=True)
        t0=time.time()
        content, meta = translate_chunk(chunk_tamil, nayanar, idx, total, headers_in_chunk)
        dt=time.time()-t0
        if not content or not content.strip():
            print(f"  FAILED chunk {idx} empty")
            content="[FAILED TRANSLATION]"
            meta={"error":"failed","choices":[{"finish_reason":"failed"}]}
        # write chunk + meta
        chunk_path.write_text(content, encoding="utf-8")
        meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2), encoding="utf-8")
        usage = meta.get("usage",{}) if isinstance(meta,dict) else {}
        cost=usage.get("cost")
        finish=meta.get("choices",[{}])[0].get("finish_reason") if isinstance(meta,dict) and meta.get("choices") else None
        print(f"  -> {len(content)} chars cost {cost} finish {finish} time {dt:.1f}s", flush=True)
        english_chunks.append(content)
        rec={"chunk":idx,"headers":headers_in_chunk,"tamil_chars":len(chunk_tamil),"english_chars":len(content),"cost":cost,"finish":finish,"duration_s":round(dt,1),"prompt_tokens":usage.get("prompt_tokens"),"completion_tokens":usage.get("completion_tokens"),"timestamp":datetime.datetime.now().isoformat()}
        instrument.append(rec)
        if finish!="stop" or len(content)<500 or "====" in content:
            anomalies.append(rec)
            print(f"  !! ANOMALY chunk {idx} finish {finish} chars {len(content)}", flush=True)
        time.sleep(1.2)

    # merge
    merged = "\n\n".join(english_chunks).strip()+"\n"
    # verify Chapter count and no ====
    has_eq="====" in merged
    ch_count=merged.count("Chapter ")
    print(f" MERGED {slug} -> {len(merged)} chars Chapters {ch_count} has==== {has_eq} anomalies {len(anomalies)}", flush=True)
    # write final english + bilingual + meta
    story_eng = base / f"{slug}_english.txt"
    story_eng.write_text(merged, encoding="utf-8")
    # aggregated meta
    agg = {"slug":slug,"nayanar":nayanar,"chunks":total,"merged_chars":len(merged),"merged_chapters":ch_count,"has_eq":has_eq,"instrument":instrument,"anomalies":anomalies,"elapsed_s":round(time.time()-t_start,1)}
    meta_agg_path = base / f"{slug}_english_meta.json"
    meta_agg_path.write_text(json.dumps(agg,ensure_ascii=False,indent=2), encoding="utf-8")
    bilingual = base / f"{slug}_bilingual.txt"
    bilingual.write_text(f"# Tamil\n\n{story_tamil}\n\n# English\n\n{merged}\n", encoding="utf-8")
    print(f" WROTE {story_eng} {story_eng.stat().st_size} + {bilingual} {bilingual.stat().st_size} + {meta_agg_path}", flush=True)
    # instrumentation file in english_real
    instr_path = english_dir / f"{slug}_english_instrumentation.json"
    instr_path.write_text(json.dumps({"nayanar":nayanar,"slug":slug,"day":DAY,"start":t_start,"end":time.time(),"elapsed_s":round(time.time()-t_start,1),"chunks":instrument,"anomalies":anomalies},ensure_ascii=False,indent=2), encoding="utf-8")
    if anomalies:
        print(f" MANUAL REVIEW {slug} anomalies {anomalies}", flush=True)
    return {"slug":slug,"chunks":total,"english_chars":len(merged),"chapters":ch_count,"anomalies":len(anomalies),"cost":sum((r.get("cost") or 0) for r in instrument)}

def main():
    total_slugs=len(SLUGS)
    wall_start=time.time()
    print(f"[ {time.strftime('%H:%M:%S')} ] Pass 2 START {total_slugs} stories chunked (limit {CHUNK_TAMIL_LIMIT}) -> english_real")
    results=[]
    last_print=time.time()
    for idx,(slug,nayanar) in enumerate(SLUGS,1):
        res = run_slug(slug, nayanar)
        results.append(res)
        # event heartbeat: after each story
        wall=time.time()-wall_start
        print(f"[ {time.strftime('%H:%M:%S')} wall {wall/60:.1f}m ] {idx}/{total_slugs} DONE {slug} {res['english_chars']} chars Chapters {res['chapters']} anomalies {res['anomalies']} cost {res['cost']:.4f}", flush=True)
        if time.time()-last_print >= HEARTBEAT_S:
            last_print=time.time()
    wall=time.time()-wall_start
    total_cost=sum(r["cost"] for r in results)
    print(f"\nPass 2 DONE wall {wall/60:.1f}m ({wall:.0f}s) cost ${total_cost:.4f} stories {total_slugs}")
    # summary
    for r in results:
        print(f" {r['slug']}: {r['chunks']} chunks {r['english_chars']} chars {r['chapters']} ch anomalies {r['anomalies']}")
    # check non-zero anomalies
    bad=[r for r in results if r["anomalies"]>0]
    if bad:
        print(f"WARN anomalies remain {bad} — review english_real/*.txt")
        sys.exit(1)

if __name__=="__main__":
    main()
