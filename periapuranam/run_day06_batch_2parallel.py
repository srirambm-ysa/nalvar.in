#!/usr/bin/env python3
"""
Batch wrapper for Day 06 — 2-parallel, 2 phases (reverted from 4-parallel after Drive stall at 6.5m).
Phase A: chandesura + karaikal (resume, 2+1 chunks already cached)
Phase B: kazharitrarivar + kannappa (kazhar 937 re-download after 160K invalid, kannappa 124 1462s valid)
Keeps throttle 2.0s + 30s stagger, POLL 30s + HEARTBEAT 300s, python -u, filesystem count, resume skip >500.
"""
import subprocess, pathlib, time, json, re, sys, os

ROOT = pathlib.Path(__file__).parent
STAGGER = 30
POLL = 30
HEARTBEAT_S = 300
LOG_DIR = ROOT / "output" / "day-06" / "logs"
PROGRESS_FILE = ROOT / "output" / "day-06" / "batch_progress.json"

def log_path(slug): return LOG_DIR / f"{slug}.log"
def slug_label(s): return s.replace("_nayanar","").replace("_"," ")

def count_progress(slug):
    tamil_dir = ROOT / "output" / "day-06" / slug / "tamil_real"
    done = 0
    if tamil_dir.exists():
        for p in tamil_dir.glob("periyapuranam-*_chunk*.txt"):
            try:
                if p.stat().st_size > 500:
                    txt = p.read_text(encoding="utf-8", errors="ignore").strip()
                    if txt and "[FAILED" not in txt:
                        done += 1
            except: pass
    total = None
    story_tamil = tamil_dir / f"{slug}_tamil.txt"
    if story_tamil.exists():
        log = tamil_dir / "transcribe_log.json"
        if log.exists():
            try:
                j=json.loads(log.read_text(encoding="utf-8"))
                total = sum(x.get("chunks",0) for x in j)
            except: pass
    lp = log_path(slug)
    cost = 0.0
    if lp.exists():
        try:
            txt = lp.read_text(encoding="utf-8", errors="ignore")
            costs = re.findall(r"cost (0\.\d+)", txt)
            cost = sum(float(c) for c in costs) if costs else 0.0
        except: pass
    eng_meta = ROOT / "output" / "day-06" / slug / f"{slug}_english_meta.json"
    if eng_meta.exists():
        try:
            j=json.loads(eng_meta.read_text(encoding="utf-8"))
            cost += float(j.get("usage",{}).get("cost",0) or 0)
        except: pass
    return done, total, cost

def run_phase(phase_name, slugs, expected):
    total_expected = sum(expected[s] for s in slugs)
    wall_start = time.time()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{time.strftime('%H:%M:%S')}] Phase {phase_name} start: {', '.join(slugs)} stagger {STAGGER}s total_expected {total_expected}ch (2-parallel)")
    procs = {}
    for i, slug in enumerate(slugs):
        if i>0:
            print(f"  stagger {STAGGER}s before {slug}...")
            time.sleep(STAGGER)
        cmd = [sys.executable, "-u", str(ROOT / f"run_{slug}.py")]
        lp = log_path(slug)
        f = open(lp, "a", encoding="utf-8", buffering=1)
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(ROOT.parent), env={**os.environ, "PYTHONUNBUFFERED":"1"})
        procs[slug]= (p,f)
        print(f"  launched {slug} pid {p.pid} -> {lp}")

    try:
        last_done = -1
        last_print = time.time()
        wall0 = time.time()
        # initial resume snapshot
        done_init = sum(count_progress(s)[0] for s in slugs)
        print(f"[{time.strftime('%H:%M:%S')} wall {(time.time()-wall0)/60:.1f}m] RESUME {done_init}/{total_expected} cached", flush=True)
        while any(p.poll() is None for p,_ in procs.values()):
            time.sleep(POLL)
            wall = time.time()-wall_start
            wall_m = wall/60
            parts=[]; done_total=0; cost_total=0.0
            for slug in slugs:
                done,total,cost = count_progress(slug)
                exp = expected.get(slug)
                tot = total if total else exp
                done_total += done
                cost_total += cost
                p,_ = procs[slug]
                state = "run" if p.poll() is None else f"exit {p.poll()}"
                parts.append(f"{slug_label(slug)} {done}/{tot} {state}")
            remaining = max(0, total_expected - done_total)
            eta_s = remaining * 24 / 2  # ~24s per chunk at 2.0s throttle with 2 workers
            eta_m = eta_s/60
            should_print = (done_total != last_done) or (time.time() - last_print >= HEARTBEAT_S)
            if should_print:
                meter = f"[{time.strftime('%H:%M:%S')} wall {wall_m:.1f}m Phase {phase_name}] {done_total}/{total_expected} {done_total/total_expected*100:.0f}%  ${cost_total:.2f}  ETA {eta_m:.0f}m  |  " + "  ".join(parts)
                print(meter, flush=True)
                last_done = done_total
                last_print = time.time()
            # write progress file (overall)
            # merge with existing overall
            try:
                existing={}
                if PROGRESS_FILE.exists():
                    existing=json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
                # update per_slug for this phase
                if "per_slug" not in existing:
                    existing["per_slug"]={}
                for s in slugs:
                    d,t,c = count_progress(s)
                    existing["per_slug"][s]= {"done": d, "total": t or expected[s], "cost": round(c,4), "pid": procs[s][0].pid, "exit": procs[s][0].poll()}
                # overall done
                all_slugs = ["chandesura_nayanar","karaikal_ammaiyaar","kazharitrarivar_nayanar","kannappa_nayanar"]
                all_expected = {"chandesura_nayanar":63,"karaikal_ammaiyaar":63,"kazharitrarivar_nayanar":98,"kannappa_nayanar":112}
                overall_done = sum(count_progress(s)[0] for s in all_slugs)
                overall_total = sum(all_expected.values())
                overall_cost = sum(count_progress(s)[2] for s in all_slugs)
                prog = {
                    "batch": "day-06-2parallel",
                    "phase": phase_name,
                    "wall_s": round(wall,1),
                    "wall_m": round(wall_m,1),
                    "done": overall_done,
                    "total_expected": overall_total,
                    "cost": round(overall_cost,4),
                    "eta_s": round(remaining * 24 / 2,1),
                    "per_slug": existing["per_slug"],
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                PROGRESS_FILE.write_text(json.dumps(prog, indent=2), encoding="utf-8")
            except: pass
        # close
        wall = time.time()-wall_start
        for slug,(p,f) in procs.items():
            f.close()
            rc = p.poll()
            print(f"  {slug} done exit {rc}")
        total_cost = sum(count_progress(s)[2] for s in slugs)
        print(f"Phase {phase_name} DONE wall {wall/60:.1f}m ({wall:.0f}s) cost ${total_cost:.4f}")
        bad = [(s,p.poll()) for s,(p,_) in procs.items() if p.poll()!=0]
        if bad:
            print(f"WARN non-zero exits {bad} — check logs/")
            return False
        return True
    except KeyboardInterrupt:
        print("\nInterrupted — terminating children...")
        for _,(p,_) in procs.items():
            try: p.terminate()
            except: pass
        sys.exit(130)

def main():
    expected = {"chandesura_nayanar":63, "karaikal_ammaiyaar":63, "kazharitrarivar_nayanar":98, "kannappa_nayanar":112}
    t0=time.time()
    # Phase A
    ok = run_phase("A-chandesura+karaikal", ["chandesura_nayanar","karaikal_ammaiyaar"], expected)
    if not ok:
        print("Phase A failed — aborting before Phase B")
        sys.exit(1)
    print(f"\n[{time.strftime('%H:%M:%S')}] Phase A complete — starting Phase B in 10s...")
    time.sleep(10)
    ok2 = run_phase("B-kazhari+kannappa", ["kazharitrarivar_nayanar","kannappa_nayanar"], expected)
    t_wall = time.time()-t0
    print(f"\nBATCH day-06-2parallel DONE overall wall {t_wall/60:.1f}m ({t_wall:.0f}s)")
    # final verify
    all_done = sum(count_progress(s)[0] for s in expected)
    all_total = sum(expected.values())
    print(f"Overall {all_done}/{all_total} chunks")
    if not ok2:
        sys.exit(1)

if __name__=="__main__":
    main()
