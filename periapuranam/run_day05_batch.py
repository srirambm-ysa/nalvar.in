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
# meter refresh — event-based (per chunk) + 5-min heartbeat; no 5-sec spam
POLL = 30
HEARTBEAT_S = 300

LOG_DIR = ROOT / "output" / "day-05" / "logs"
PROGRESS_FILE = ROOT / "output" / "day-05" / "batch_progress.json"

def log_path(slug): return LOG_DIR / f"{slug}.log"
def slug_label(s): return s.replace("_nayanar","").replace("_"," ")

def count_progress(slug):
    """count via filesystem (chunk txt files) + log cost. Returns (done,total,cost_done)"""
    tamil_dir = ROOT / "output" / "day-05" / slug / "tamil_real"
    # done = chunk txt files >500 bytes and not FAILED (event-based truth)
    done = 0
    if tamil_dir.exists():
        for p in tamil_dir.glob("periyapuranam-*_chunk*.txt"):
            try:
                if p.stat().st_size > 500:
                    txt = p.read_text(encoding="utf-8", errors="ignore").strip()
                    if txt and "[FAILED" not in txt:
                        done += 1
            except: pass
    # total: from transcribe_log if story done else expected
    total = None
    story_tamil = tamil_dir / f"{slug}_tamil.txt"
    if story_tamil.exists():
        log = tamil_dir / "transcribe_log.json"
        if log.exists():
            try:
                j=json.loads(log.read_text(encoding="utf-8"))
                total = sum(x.get("chunks",0) for x in j)
            except: pass
    # cost: parse log for cost (only when available, no spam)
    lp = log_path(slug)
    cost = 0.0
    if lp.exists():
        try:
            txt = lp.read_text(encoding="utf-8", errors="ignore")
            costs = re.findall(r"cost (0\.\d+)", txt)
            cost = sum(float(c) for c in costs) if costs else 0.0
        except: pass
    eng_meta = ROOT / "output" / "day-05" / slug / f"{slug}_english_meta.json"
    if eng_meta.exists():
        try:
            j=json.loads(eng_meta.read_text(encoding="utf-8"))
            cost += float(j.get("usage",{}).get("cost",0) or 0)
        except: pass
    return done, total, cost

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
        cmd = [sys.executable, "-u", str(ROOT / f"run_{slug}.py")]
        lp = log_path(slug)
        # do NOT truncate if resume: keep existing log and append (preserves cached skip visibility)
        # only truncate if day05 batch1 logs (murthi etc) — for batch2 we append
        f = open(lp, "a", encoding="utf-8", buffering=1)
        # keep handle to close later
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(ROOT.parent), env={**os.environ, "PYTHONUNBUFFERED":"1"})
        procs[slug]= (p,f)
        print(f"  launched {slug} pid {p.pid} -> {lp} (-u unbuffered, append)")

    # live meter — event-based: only print when done increments or every 5 mins
    try:
        last_done = -1
        last_print = time.time()
        # initial snapshot
        wall = time.time()-wall_start
        done_total_init = sum(count_progress(s)[0] for s in SLUGS)
        print(f"[{time.strftime('%H:%M:%S')} wall {wall/60:.1f}m] RESUME {done_total_init}/{total_expected} chunks already cached (will skip API)", flush=True)
        while any(p.poll() is None for p,_ in procs.values()):
            time.sleep(POLL)
            wall = time.time()-wall_start
            wall_m = wall/60
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
            remaining = max(0, total_expected - done_total)
            eta_s = remaining * 22 / 3 if remaining else 0
            eta_m = eta_s/60
            # only print on progress or heartbeat (5-min)
            should_print = (done_total != last_done) or (time.time() - last_print >= HEARTBEAT_S)
            if should_print:
                meter = f"[{time.strftime('%H:%M:%S')} wall {wall_m:.1f}m] {done_total}/{total_expected} {done_total/total_expected*100:.0f}%  ${cost_total:.2f}  ETA {eta_m:.0f}m  |  " + "  ".join(parts)
                print(meter, flush=True)
                last_done = done_total
                last_print = time.time()
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
