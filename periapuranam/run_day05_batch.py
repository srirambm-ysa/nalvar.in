#!/usr/bin/env python3
"""
Batch wrapper for Day 05 remaining 3 (Amar-Niti, Eri-Pattha, Siruthonda)
with wall-clock tracking + live progress meter.
Reuses existing per-slug runners (run_*.py) — no change to transcription logic.
Logs are per-slug as before, plus batch_progress.json + console meter.
"""
import subprocess, pathlib, time, json, re, sys, os

ROOT = pathlib.Path(__file__).parent
BATCH = "day-05-batch2"
SLUGS = ["amar_niti_nayanar", "eri_pattha_nayanar", "siruthonda_nayanar"]
# stagger between launches (s) — matches process_instructions 30s discussion
STAGGER = 30
# meter refresh
POLL = 5

LOG_DIR = ROOT / "output" / "day-05" / "logs"
PROGRESS_FILE = ROOT / "output" / "day-05" / "batch_progress.json"

def log_path(slug): return LOG_DIR / f"{slug}.log"
def slug_label(s): return s.replace("_nayanar","").replace("_"," ")

def count_progress(slug):
    """parse log for done/total/cost. Returns (done,total,cost_done)"""
    lp = log_path(slug)
    if not lp.exists():
        return 0, None, 0.0
    txt = lp.read_text(encoding="utf-8", errors="ignore")
    # done = count of "-> ... chars, cost" lines (successful transcribes + cached skip)
    # also cached lines have "skip API"
    # total estimated from "chunk 1/4" highest denominator seen
    done = txt.count("-> transcribing")  # launched
    # completed: lines with "chars," after transcribing or cached skip
    completed = len(re.findall(r"cached \d+ chars skip API|-> \d+ chars, cost", txt))
    # total: max denominator from "chunk X/Y"
    totals = re.findall(r"chunk \d+/(\d+)", txt)
    total = max(map(int, totals)) if totals else None
    # but story has multiple seq files, so total above is per-seq, not per-story.
    # Better estimate total per-story from transcribe_log if exists, else None.
    # For live, sum of per-seq totals: count distinct seq blocks? Use "MERGED seq" count?
    # Fallback: count expected from day_wise_plan — hardcode for batch2.
    # We know batch2: 13+13+13 files ~45ch each => ~135ch. Use log MERGED count * avg.
    # Instead show per-seq progress aggregated: completed is actual done chunks, show as completed.
    # For meter total, use transcribe_log total if story done, else estimate.
    story_tamil = ROOT / "output" / "day-05" / slug / "tamil_real" / f"{slug}_tamil.txt"
    if story_tamil.exists():
        # story done — total is known via log
        log = ROOT / "output" / "day-05" / slug / "tamil_real" / "transcribe_log.json"
        if log.exists():
            try:
                j=json.loads(log.read_text(encoding="utf-8"))
                total = sum(x.get("chunks",0) for x in j)
            except: pass
    costs = re.findall(r"cost (0\.\d+)", txt)
    cost = sum(float(c) for c in costs) if costs else 0.0
    # include instrumentation EN cost if done
    eng_meta = ROOT / "output" / "day-05" / slug / f"{slug}_english_meta.json"
    if eng_meta.exists():
        try:
            j=json.loads(eng_meta.read_text(encoding="utf-8"))
            cost += float(j.get("usage",{}).get("cost",0) or 0)
        except: pass
    return completed, total, cost

def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # hard-coded expected totals from prior run template (for ETA when total unknown)
    expected = {"amar_niti_nayanar":45, "eri_pattha_nayanar":45, "siruthonda_nayanar":46}
    total_expected = sum(expected.values())
    procs = {}
    wall_start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Batch {BATCH} start: {', '.join(SLUGS)} stagger {STAGGER}s total_expected {total_expected}ch")
    for i, slug in enumerate(SLUGS):
        if i>0:
            print(f"  stagger {STAGGER}s before {slug}...")
            time.sleep(STAGGER)
        cmd = [sys.executable, str(ROOT / f"run_{slug}.py")]
        lp = log_path(slug)
        # truncate log for fresh batch2 (keep old as .bak if exists and non-empty)
        if lp.exists() and lp.stat().st_size>0:
            bak = lp.with_suffix(".log.bak")
            if not bak.exists():
                lp.rename(bak)
        f = open(lp, "w", encoding="utf-8", buffering=1)
        # keep handle to close later
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(ROOT.parent))
        procs[slug]= (p,f)
        print(f"  launched {slug} pid {p.pid} -> {lp}")

    # live meter
    try:
        while any(p.poll() is None for p,_ in procs.values()):
            time.sleep(POLL)
            wall = time.time()-wall_start
            parts=[]
            done_total=0
            cost_total=0.0
            for slug in SLUGS:
                done,total,cost = count_progress(slug)
                exp = expected.get(slug)
                tot = total if total else exp
                done_total += done
                cost_total += cost
                p,_ = procs[slug]
                state = "run" if p.poll() is None else f"exit {p.poll()}"
                parts.append(f"{slug_label(slug)} {done}/{tot} {state}")
            # eta: avg cost per chunk ~0.0096 + 22s per chunk => remaining*22s / parallelism(3)
            # wall tracks real, eta = remaining*22/3
            remaining = max(0, total_expected - done_total)
            # parallel factor 3 but staggered, approx 22s per chunk /3
            eta_s = remaining * 22 / 3 if remaining else 0
            wall_m = wall/60
            eta_m = eta_s/60
            meter = f"[{time.strftime('%H:%M:%S')} wall {wall_m:.1f}m] {done_total}/{total_expected} {done_total/total_expected*100:.0f}%  ${cost_total:.2f}  ETA {eta_m:.0f}m  |  " + "  ".join(parts)
            print(meter, flush=True)
            # write progress file (for resume/dashboard)
            prog = {
                "batch": BATCH,
                "wall_s": round(wall,1),
                "wall_m": round(wall_m,1),
                "done": done_total,
                "total_expected": total_expected,
                "cost": round(cost_total,4),
                "eta_s": round(eta_s,1),
                "per_slug": {s: {"done": count_progress(s)[0], "total": count_progress(s)[1] or expected[s], "cost": round(count_progress(s)[2],4), "pid": procs[s][0].pid, "exit": procs[s][0].poll()} for s in SLUGS},
                "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            try:
                PROGRESS_FILE.write_text(json.dumps(prog, indent=2), encoding="utf-8")
            except: pass
        # final
        wall = time.time()-wall_start
        for slug,(p,f) in procs.items():
            f.close()
            rc = p.poll()
            print(f"  {slug} done exit {rc}")
        total_cost = sum(count_progress(s)[2] for s in SLUGS)
        print(f"Batch {BATCH} DONE wall {wall/60:.1f}m ({wall:.0f}s) cost ${total_cost:.4f} -> {PROGRESS_FILE}")
        # final progress
        try:
            prog=json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            prog["wall_s"]=round(wall,1)
            prog["done_wall_m"]=round(wall/60,1)
            prog["final"]=True
            PROGRESS_FILE.write_text(json.dumps(prog, indent=2), encoding="utf-8")
        except: pass
        # check exit codes
        bad = [(s,p.poll()) for s,(p,_) in procs.items() if p.poll()!=0]
        if bad:
            print(f"WARN non-zero exits {bad} — check logs/")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted — terminating children...")
        for _,(p,_) in procs.items():
            try: p.terminate()
            except: pass
        sys.exit(130)

if __name__=="__main__":
    main()
