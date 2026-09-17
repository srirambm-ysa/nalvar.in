#!/usr/bin/env python3
"""
Day 06 remaining 3-phase runner for Kazharitrarivar 28F + Kannappa 32F
Phase A: 2-parallel download (host-limited, 120s 3x retry) — proven stable
Phase B: 4-parallel transcribe Tamil (first test of 4-parallel LLM, no host) — instrumentation + _errors.log gate
Phase C: 4-parallel chunked translate 60K (first test of 4-parallel translate) — instrumentation

Usage:
  python -u periapuranam/run_day06_remaining_3phase.py           # runs A->B->C sequentially
  python -u periapuranam/run_day06_remaining_3phase.py --phase A # only A
  python -u periapuranam/run_day06_remaining_3phase.py --phase B # only B (requires A done)
  python -u periapuranam/run_day06_remaining_3phase.py --phase C # only C (requires B done)

Instrumentation for 4-parallel first-time:
- per-slug logs: output/day-06/logs/{slug}_phase{A,B,C}.log (unbuffered python -u)
- batch_progress.json: overall done/total/cost/eta + per_slug {done,total,cost,exit,finish}
- per-slug instrumentation: tamil_real/{slug}_instrumentation.json (per_chunk + anomalies)
- per-slug errors: tamil_real/{slug}_errors.log (dur-aware HUGE/TINY/EMPTY + tails)
- Phase B gate: if any anomalies -> pause before C, batch exits 1 for human review
- Phase C gate: check has==== false, Chapter count, finish stop
"""
import subprocess, pathlib, time, json, re, sys, os, argparse

ROOT = pathlib.Path(__file__).parent
DAY = "day-06"
LOG_DIR = ROOT / "output" / DAY / "logs"
PROGRESS_FILE = ROOT / "output" / DAY / "batch_progress.json"
STAGGER_A = 10  # small stagger for download 2-parallel
STAGGER_B = 30  # throttle stagger for LLM
STAGGER_C = 15
POLL = 30
HEARTBEAT_S = 300

REMAINING = {
    "kazharitrarivar_nayanar": {"files":28, "est_chunks":98},
    "kannappa_nayanar": {"files":32, "est_chunks":112},
}
ALL_EXPECTED = {"chandesura_nayanar":63,"karaikal_ammaiyaar":63,"kazharitrarivar_nayanar":98,"kannappa_nayanar":112}

def log_path(slug, phase): return LOG_DIR / f"{slug}_phase{phase}.log"
def slug_label(s): return s.replace("_nayanar","").replace("_"," ")

def count_progress_tamil(slug):
    tamil_dir = ROOT / "output" / DAY / slug / "tamil_real"
    done=0; total=None; cost=0.0
    if tamil_dir.exists():
        for p in tamil_dir.glob("periyapuranam-*_chunk*.txt"):
            try:
                if p.stat().st_size>500:
                    txt=p.read_text(encoding="utf-8", errors="ignore").strip()
                    if txt and "[FAILED" not in txt: done+=1
            except: pass
        # total from transcribe_log or expected
        log=tamil_dir/"transcribe_log.json"
        if log.exists():
            try:
                j=json.loads(log.read_text(encoding="utf-8"))
                total=sum(x.get("chunks",0) for x in j)
            except: pass
        instr=tamil_dir/f"{slug}_instrumentation.json"
        if instr.exists():
            try:
                j=json.loads(instr.read_text(encoding="utf-8"))
                for rec in j.get("per_chunk",[]):
                    if rec.get("cost") is not None:
                        cost+=float(rec["cost"] or 0)
            except: pass
    # fallback total
    if total is None: total=REMAINING.get(slug,{}).get("est_chunks")
    # also try log file cost scan
    lp=log_path(slug,"B")
    if lp.exists():
        try:
            txt=lp.read_text(encoding="utf-8", errors="ignore")
            costs=re.findall(r"cost (0\.\d+)", txt)
            # not accurate, but use instrumentation instead
            pass
        except: pass
    return done, total, cost

def count_progress_english(slug):
    eng_dir = ROOT/"output"/DAY/slug/"english_real"
    tamil_file = ROOT/"output"/DAY/slug/"tamil_real"/f"{slug}_tamil.txt"
    done=0; total=None
    if eng_dir.exists():
        done=len(list(eng_dir.glob(f"{slug}_english_chunk*.txt")))
        # total from instr
        instr=eng_dir/f"{slug}_english_instrumentation.json"
        if instr.exists():
            try: total=len(json.loads(instr.read_text(encoding="utf-8")).get("chunks",[]))
            except: pass
    if total is None and tamil_file.exists():
        try:
            txt=tamil_file.read_text(encoding="utf-8")
            groups=re.split(r'(?=^Chapter \d{2} —)', txt, flags=re.M)
            ch=[p for p in groups if p.strip().startswith("Chapter")]
            cur=""; groups2=[]
            for chp in ch:
                if len(cur)+len(chp)>60000 and cur: groups2.append(cur.strip()); cur=chp
                else: cur=cur+"\n\n"+chp if cur else chp
            if cur.strip(): groups2.append(cur.strip())
            total=len(groups2)
        except: pass
    return done, total

def launch_phase(phase, slugs, stagger, max_workers=4):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if phase=="A":
        total_expected=sum(REMAINING[s]["files"] for s in slugs)  # 28+32=60 files
    elif phase=="B":
        total_expected=sum(REMAINING[s]["est_chunks"] for s in slugs)  # 98+112=210 chunks
    elif phase=="C":
        total_expected=0
        for s in slugs:
            _,t=count_progress_english(s)
            total_expected+=(t or 5)  # ~5 chunks per story at 60K
        if total_expected==0:
            total_expected=sum(5 for _ in slugs)  # fallback 10
    else:
        total_expected=sum(REMAINING[s]["files"] for s in slugs)
    print(f"\n[{time.strftime('%H:%M:%S')}] Phase {phase} start: {', '.join(slugs)} stagger {stagger}s max_workers {max_workers}", flush=True)
    procs={}
    for i, slug in enumerate(slugs):
        if i>0:
            print(f"  stagger {stagger}s before {slug}...", flush=True)
            time.sleep(stagger)
        cmd=[sys.executable, "-u", str(ROOT / f"run_{slug}.py"), "--phase", phase]
        lp=log_path(slug, phase)
        # append, unbuffered
        f=open(lp, "a", encoding="utf-8", buffering=1)
        f.write(f"\n=== Phase {phase} {slug} {time.strftime('%Y-%m-%d %H:%M:%S')} cmd={' '.join(cmd)} ===\n")
        f.flush()
        env={**os.environ, "PYTHONUNBUFFERED":"1"}
        p=subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(ROOT.parent), env=env)
        procs[slug]=(p,f,lp)
        print(f"  launched {slug} pid {p.pid} -> {lp}", flush=True)
        if len(procs)>=max_workers:
            print(f"  max_workers {max_workers} reached, launching remaining after stagger...", flush=True)

    wall_start=time.time()
    last_done=-1; last_print=time.time()
    if phase=="A":
        done_init=sum(len(list((ROOT/"output"/DAY/s/"audio").glob("*.mp3"))) if (ROOT/"output"/DAY/s/"audio").exists() else 0 for s in slugs)
    elif phase=="B":
        done_init=sum(count_progress_tamil(s)[0] for s in slugs)
    else:
        done_init=sum(count_progress_english(s)[0] for s in slugs)
    print(f"[{time.strftime('%H:%M:%S')} wall 0.0m] RESUME {done_init}/{total_expected} cached ({done_init/total_expected*100:.0f}%)", flush=True)
    try:
        while any(p.poll() is None for p,_,_ in procs.values()):
            time.sleep(POLL)
            wall=time.time()-wall_start
            wall_m=wall/60
            parts=[]; done_total=0; cost_total=0.0
            for slug in slugs:
                if phase=="B":
                    done,total,cost=count_progress_tamil(slug)
                elif phase=="C":
                    done,total=count_progress_english(slug)
                    cost=0
                    # sum english cost from meta
                    eng_meta=ROOT/"output"/DAY/slug/f"{slug}_english_meta.json"
                    if eng_meta.exists():
                        try: cost=sum(float(x.get("cost") or 0) for x in json.loads(eng_meta.read_text(encoding="utf-8")).get("instrument",[]))
                        except: pass
                else:
                    # Phase A download progress = files present
                    aud=ROOT/"output"/DAY/slug/"audio"
                    done=len(list(aud.glob("*.mp3"))) if aud.exists() else 0
                    total=REMAINING[slug]["files"]
                    cost=0
                exp=REMAINING[slug]["est_chunks"] if phase=="B" else (REMAINING[slug]["files"] if phase=="A" else 5)
                tot=total if total else exp
                done_total+=done
                cost_total+=cost
                p,_,_=procs[slug]
                state="run" if p.poll() is None else f"exit {p.poll()}"
                parts.append(f"{slug_label(slug)} {done}/{tot} {state}")
            remaining=max(0, total_expected - done_total)
            if phase=="B":
                eta_s=remaining*24 / max_workers  # 24s per chunk / workers
            elif phase=="C":
                eta_s=remaining*80 / max_workers  # 80s per English chunk
            else:
                eta_s=remaining*8  # ~8s per download at 2-parallel, ~4s per file effective
            eta_m=eta_s/60
            should_print=(done_total!=last_done) or (time.time()-last_print>=HEARTBEAT_S)
            if should_print:
                meter=f"[{time.strftime('%H:%M:%S')} wall {wall_m:.1f}m Phase {phase}] {done_total}/{total_expected} {done_total/total_expected*100:.0f}% ${cost_total:.2f} ETA {eta_m:.0f}m | "+"  ".join(parts)
                print(meter, flush=True)
                last_done=done_total; last_print=time.time()
            # write progress
            try:
                existing={}
                if PROGRESS_FILE.exists():
                    try: existing=json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
                    except: existing={}
                if "per_slug" not in existing: existing["per_slug"]={}
                for s in slugs:
                    if phase=="B":
                        d,t,c=count_progress_tamil(s)
                    elif phase=="C":
                        d,t=count_progress_english(s)
                        c=0
                    else:
                        d=len(list((ROOT/"output"/DAY/s/"audio").glob("*.mp3"))) if (ROOT/"output"/DAY/s/"audio").exists() else 0
                        t=REMAINING[s]["files"]; c=0
                    existing["per_slug"][s]={"done":d,"total":t or (REMAINING[s]["est_chunks"] if phase=="B" else (REMAINING[s]["files"] if phase=="A" else 5)),"cost":round(c,4),"pid":procs[s][0].pid,"exit":procs[s][0].poll(),"phase":phase}
                if phase=="A":
                    overall_done=sum(len(list((ROOT/"output"/DAY/s/"audio").glob("*.mp3"))) if (ROOT/"output"/DAY/s/"audio").exists() else 0 for s in ALL_EXPECTED)
                elif phase=="B":
                    overall_done=sum(count_progress_tamil(s)[0] for s in ALL_EXPECTED)
                else:
                    overall_done=sum(count_progress_english(s)[0] for s in ALL_EXPECTED)
                prog={"batch":"day-06-remaining-3phase","phase":phase,"wall_s":round(wall,1),"wall_m":round(wall_m,1),"done":done_total,"total_expected":total_expected,"cost":round(cost_total,4),"per_slug":existing["per_slug"],"updated":time.strftime("%Y-%m-%d %H:%M:%S")}
                PROGRESS_FILE.write_text(json.dumps(prog,indent=2), encoding="utf-8")
            except Exception as e:
                print(f" progress write fail {e}", flush=True)
        wall=time.time()-wall_start
        for slug,(p,f,lp) in procs.items():
            f.close()
            rc=p.poll()
            print(f"  {slug} phase {phase} done exit {rc} log {lp}", flush=True)
        bad=[(s,p.poll()) for s,(p,_,_) in procs.items() if p.poll()!=0]
        if bad:
            print(f"WARN Phase {phase} non-zero exits {bad} — check logs/{phase}", flush=True)
            return False
        print(f"Phase {phase} DONE wall {wall/60:.1f}m ({wall:.0f}s)", flush=True)
        return True
    except KeyboardInterrupt:
        print("\nInterrupted — terminating children...", flush=True)
        for _,(p,_,_) in procs.items():
            try: p.terminate()
            except: pass
        sys.exit(130)

def verify_phaseA():
    print("\n=== Verify Phase A (download) ===", flush=True)
    ok=True
    for slug in REMAINING:
        aud=ROOT/"output"/DAY/slug/"audio"
        files=sorted(aud.glob("*.mp3")) if aud.exists() else []
        exp=REMAINING[slug]["files"]
        print(f" {slug}: {len(files)}/{exp} files", flush=True)
        if len(files)!=exp: ok=False
        for f in files:
            if f.stat().st_size < 1*1024*1024:
                print(f"  FAIL {f.name} too small {f.stat().st_size}", flush=True); ok=False
            r=subprocess.run(["ffprobe","-v","warning","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", str(f)], capture_output=True, text=True)
            if r.returncode!=0 or r.stderr.strip()!="":
                print(f"  WARN {f.name} ffprobe warning {r.stderr[:200]}", flush=True)
    print(f"Phase A verify {'PASS' if ok else 'FAIL'}", flush=True)
    return ok

def verify_phaseB():
    print("\n=== Verify Phase B (Tamil) ===", flush=True)
    ok=True
    for slug in REMAINING:
        tamil_file=ROOT/"output"/DAY/slug/"tamil_real"/f"{slug}_tamil.txt"
        instr=ROOT/"output"/DAY/slug/"tamil_real"/f"{slug}_instrumentation.json"
        errlog=ROOT/"output"/DAY/slug/"tamil_real"/f"{slug}_errors.log"
        if not tamil_file.exists(): print(f"  FAIL {slug} missing tamil.txt", flush=True); ok=False; continue
        txt=tamil_file.read_text(encoding="utf-8")
        has_eq="====" in txt
        ch_count=len(re.findall(r"^Chapter \d{2}", txt, flags=re.M))
        exp=REMAINING[slug]["files"]
        print(f" {slug}: {len(txt)} chars {ch_count}/{exp} ch has==== {has_eq} {tamil_file.stat().st_size} bytes", flush=True)
        if has_eq: print(f"  FAIL has ====", flush=True); ok=False
        if ch_count!=exp: print(f"  FAIL Chapter count {ch_count}!={exp}", flush=True); ok=False
        if instr.exists():
            j=json.loads(instr.read_text(encoding="utf-8"))
            anomalies=j.get("anomalies",[])
            print(f"  instrumentation anomalies {len(anomalies)}", flush=True)
            if anomalies:
                print(f"  !! ANOMALIES present -> {errlog} — manual review required", flush=True)
                for a in anomalies[:5]: print(f"    {a}", flush=True)
                ok=False
        else: print(f"  WARN no instrumentation", flush=True)
        if errlog.exists():
            print(f"  errors.log exists {errlog.stat().st_size} bytes — flagged", flush=True)
    print(f"Phase B verify {'PASS' if ok else 'FLAGGED (needs manual fix before C)'}", flush=True)
    return ok

def verify_phaseC():
    print("\n=== Verify Phase C (English) ===", flush=True)
    ok=True
    for slug in REMAINING:
        eng=ROOT/"output"/DAY/slug/f"{slug}_english.txt"
        tamil=ROOT/"output"/DAY/slug/"tamil_real"/f"{slug}_tamil.txt"
        meta=ROOT/"output"/DAY/slug/f"{slug}_english_meta.json"
        eng_dir=ROOT/"output"/DAY/slug/"english_real"
        if not eng.exists(): print(f"  FAIL {slug} missing english.txt", flush=True); ok=False; continue
        txt=eng.read_text(encoding="utf-8")
        has_eq="====" in txt
        ch_count=len(re.findall(r"^Chapter \d{2}", txt, flags=re.M))
        exp=REMAINING[slug]["files"]
        print(f" {slug}: {len(txt)} chars {ch_count}/{exp} ch has==== {has_eq} {eng.stat().st_size} bytes", flush=True)
        if has_eq: print(f"  FAIL has ====", flush=True); ok=False
        if ch_count!=exp: print(f"  FAIL Chapter {ch_count}!={exp}", flush=True); ok=False
        # finish stop check
        if eng_dir.exists():
            for mf in sorted(eng_dir.glob("*_meta.json")):
                try:
                    j=json.loads(mf.read_text(encoding="utf-8"))
                    finish=j.get("choices",[{}])[0].get("finish_reason") if j.get("choices") else j.get("finish")
                    if finish and finish!="stop":
                        print(f"  FAIL {mf.name} finish {finish}", flush=True); ok=False
                except: pass
        if meta.exists():
            j=json.loads(meta.read_text(encoding="utf-8"))
            print(f"  meta chunks {j.get('chunks')} merged_chapters {j.get('merged_chapters')} has_eq {j.get('has_eq')}", flush=True)
        bil=ROOT/"output"/DAY/slug/f"{slug}_bilingual.txt"
        print(f"  bilingual {bil.exists()} {bil.stat().st_size/1024:.0f}KB" if bil.exists() else "  bilingual missing", flush=True)
    print(f"Phase C verify {'PASS' if ok else 'FAIL'}", flush=True)
    return ok

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--phase", default="all", help="A,B,C,all")
    args=parser.parse_args()
    phase=args.phase.upper()
    phases=[]
    if phase=="ALL": phases=["A","B","C"]
    else: phases=[p.strip() for p in phase.split(",")]

    t0=time.time()
    slugs=list(REMAINING.keys())
    for ph in phases:
        if ph=="A":
            ok=launch_phase("A", slugs, STAGGER_A, max_workers=2)
            if not ok: print("Phase A failed abort"); sys.exit(1)
            if not verify_phaseA(): print("Phase A verify FAIL abort"); sys.exit(1)
        elif ph=="B":
            ok=launch_phase("B", slugs, STAGGER_B, max_workers=4)
            # verify even if non-zero, show instrumentation
            passed=verify_phaseB()
            # aggregate batch 4-parallel instrumentation summary
            print(f"\n=== Batch 4-parallel Phase B summary ===", flush=True)
            print(f"  launched {len(slugs)} workers with max_workers 4 (effective {len(slugs)}), stagger {STAGGER_B}s", flush=True)
            print(f"  POLL {POLL}s HEARTBEAT {HEARTBEAT_S}s python -u filesystem count + per-chunk instrumentation", flush=True)
            if not passed:
                print(f"Phase B flagged anomalies — STOP before Phase C for human review (per transcription-strategy.md:77)", flush=True)
                if "C" in phases:
                    print(f"Requested phases include C — aborting before C", flush=True)
                    sys.exit(1)
                else:
                    sys.exit(2)  # flagged but not fatal
            if not ok: sys.exit(1)
        elif ph=="C":
            ok=launch_phase("C", slugs, STAGGER_C, max_workers=4)
            passed=verify_phaseC()
            if not ok or not passed: print("Phase C FAIL"); sys.exit(1)
        else: print(f"unknown phase {ph}"); sys.exit(1)
        time.sleep(5)
    print(f"\nALL PHASES {phases} DONE wall {(time.time()-t0)/60:.1f}m", flush=True)
    # final batch progress
    print(f"Check per-slug logs: {LOG_DIR}/{{slug}}_phase{{A,B,C}}.log", flush=True)
    print(f"Instrumentation: tamil_real/*_instrumentation.json + english_real/*_english_instrumentation.json", flush=True)
    print(f"Errors: tamil_real/*_errors.log (dur-aware HUGE/TINY/EMPTY)", flush=True)

if __name__=="__main__":
    main()
