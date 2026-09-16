# Transcription Strategy — 3-Phase Pipeline (from Day07 onwards)

**Baselined:** 2026-09-16 from Day06 Phase A+B 36F (`chandesura 18F 66ch 206K`, `karaikal 18F 64ch 198K`) 2-parallel 40.5m + 9.6m, fixes `246 HUGE 37k/50k` (header 1064s vs valid 510s empty mp3 395B), `493 TINY 22->3438`, `251/261 tails 0` silence. Prior strategy: `docs/download_strategy.md:1` + `periapuranam/lessons-learnt.md:1` single runner `download+chunk+transcribe+translate`. New strategy isolates host-dependent download from LLM phases to allow 3-4 parallel LLM without Drive throttling.

## 1. Why 3 Phases

- **Host bottleneck:** `drive.usercontent.google.com` `GET ?id={fid}&export=download` with `confirm` token. Day06 4-parallel download failed: `kazhar 937 160K Invalid data` + `chandesura 246 Read timed out` + `ConnectionReset 10054` on OpenRouter. Manual re-test `curl 120s` succeeded solo, failed under 4 concurrent. 2-parallel succeeded after `timeout 60->120s` `3× retry` `periapuranam/templates/run_nayanar_template.py:28`.
- **LLM bottleneck separate:** `POST https://openrouter.ai/api/v1/chat/completions` `google/gemini-2.5-flash` `1.2-2.0s throttle` `≤20 req/min`. 4 transcribe workers → `4×2.5=10 req/min` safe, but only if not competing with 4 concurrent Drive streams.
- **Separation wins:** Phase A (download, no LLM) completes first, verifies `>1 MB` + `ffprobe -show_entries format=duration` vs `stream=duration` + `filesize/duration mismatch` warning (as 246 `1064s header vs 510s valid`). Phase B/C then run 3-4 parallel on local `audio/*.mp3` — no host dependency, can saturate LLM rate safely. Measured: Phase A 36F 18M avg ~3s/file → `108s` sequential, Phase B 130ch `22s avg` → `47m seq / 12m 4-worker`, Phase C 8 chunks `80s avg` → `10m seq / 3m 4-worker`.

## 2. Phase Definitions

### Phase A — Download Only (host-dependent, no LLM)

- **Input:** `DEFAULT_SEQ_FID=[(seq, fid),...]` from `periapuranam/day_wise_plan.xlsx` `Day 6/7` `Folder Slug`.
- **Output:** `periapuranam/output/<DAY>/<slug>/audio/periyapuranam-SEQ-fid.mp3` (`14-20 MB`, `600-1250s`).
- **Runner:** `periapuranam/run_<slug>.py --phase A` or `periapuranam/templates/run_nayanar_template.py:28` extracted `download_drive()` loop only. No `ffmpeg`, no `transcribe`.
- **Logic:** `BASE = output / DAY / SLUG` `DAY="day-07"` etc. For each `fid`: if `dest.exists() and size>1M` and `ffprobe duration` matches `stream` (no `growing file` warning) skip, else `download_drive(fid, dest)` with `3× retry timeout 120s backoff 5*try` `total>1M` else `raise` + delete partial. No `sys.exit(1)` on first failure — retry then fail batch.
- **Idempotent:** Skip if `>1M` and `ffprobe` ok. Re-run same phase to fill missing.
- **Parallel:** Limit to `2` concurrent downloads (proven stable) or `4` with `30s stagger` + `retry` — Day06 4× failed, 2× succeeded. Recommend `2` for Phase A (host-limited), wall `96F → ~5m` at 2×.
- **Verification before B:** `ls audio/*.mp3 | wc` == `Files` (18/28/32), each `ffprobe stream == format` and `no 395B` (i.e., `>1M`), `transcribe_log.json` not required yet.

### Phase B — Chunk + Transcribe Tamil (LLM, no host)

- **Input:** `audio/*.mp3` already verified.
- **Output:** `tamil_real/periyapuranam-SEQ_chunk*.txt` `>500B` `not [FAILED]` + `periyapuranam-SEQ-tamil-real.txt` + `tamil_real/<slug>_tamil.txt` `Chapter 01..N` `"\n\n"` no `====` + `tamil_real/transcribe_log.json` + `tamil_real/<slug>_instrumentation.json` (`per_chunk` `cost`, `finish`, `dur`, `flag`).
- **Runner:** `--phase B` reuses `get_duration()`, `make_chunk()` `ffmpeg -ss offset -i -t 300 -c:a libmp3lame -b:a 64k` → `C:/Temp/opencode/<slug>_chunks/` `~2.3 MB/300s`, `~1s/chunk`, then `transcribe_chunk()` `temperature 0.1 max_tokens 12000` `POST gemini-2.5-flash` `data:audio/mpeg;base64` `image_url`, `3× retry` `FATAL BUDGET 402/403 exit2`, `1.2-2.0s throttle`.
- **Key fixes from Day06:**
  - `chunk_txt_cached` resume skip `>500` and `not [FAILED]` `len>30` `continue` — saves `$0.36` on resume.
  - `dur-aware anomaly` `min 6c/s max 20c/s+500` flags `HUGE/TINY/EMPTY/REPEAT` `periapuranam/templates/run_nayanar_template.py:91` (e.g., `246c02 37492 HUGE_dur300_exp6500 finish:length` vs empty mp3 395B).
  - Detect empty chunk mp3 `<10K` or `ffprobe` fail → skip chunk, adjust `chunks = actual` (as 246 `4→2` re-merged `255K→5827`).
  - `make_chunk` must handle cover-image `mp3` with `attached pic` stream — use `-map 0:a` or `-vn` if `Output file is empty` (observed 246 `395B` case).
- **Parallel:** **3 or 4 workers safe** (no Drive). Day06 `2× 130ch 40.5m` → `4× ≈20m` at `2.0s throttle +30s stagger` `POLL 30s HEARTBEAT 300s` `python -u` `filesystem count` `batch_progress.json`. Rate `10 req/min <20`. Recommend `4-parallel` for Phase B (e.g., `kazhar 28F 98ch + kannappa 32F 112ch + next 2`). If `ConnectionReset 10054` seen (as 493c01), retry loop recovers.
- **Verification before C:** `contains '===='==false`, `Chapter 01..N == files` (18/28/32), `finish:stop` for all, `0 HUGE` (or HUGE removed), `instrumentation anomalies` reviewed (tail `0` empty like `251c03 75s 0` may be silence — keep flagged but not blocking if consistent 0 on retry).

### Phase C — Chunk + Translate English (LLM, no host)

- **Input:** `tamil_real/<slug>_tamil.txt` verified.
- **Output:** `english_real/<slug>_english_chunk*.txt` `>500` `finish:stop` + `<slug>_english.txt` `Chapter 01..N` preserved no `====` + `<slug>_english_meta.json` + `<slug>_bilingual.txt` `# Tamil + # English`.
- **Runner:** `--phase C` uses `CHUNK_TAMIL_LIMIT 60000` `periapuranam/run_day05_translate.py:22` / `run_day06_translate.py:15` — split on `^Chapter \d{2} —` accumulate `>60K` cut, fallback `80K` mid-split. Each chunk `prompt 60K Tamil ~20K tokens` `temperature 0.4 max_tokens 30000` translates to `~50K English`. For `206K Chandesura →4 chunks 57878+53521+56792+37983 → 56509+53876+55931+40970 207K 18ch`, `198K Karaikal →4 chunks 59579+50211+47419+41256 → 58747+45746+45487+41962 191K`. Single-call `30000` truncated `finish:length 138K/125K` → must chunk.
- **Idempotent resume:** if `english_real/*_chunk*.txt >500` and `meta finish:stop` and `len>1000` skip API.
- **Parallel:** **3 or 4 workers safe** (no host, only translate calls). Day06 `8 chunks 80s avg` → `10m seq / 2.5m 4-worker`. Each chunk `1.2s` throttle. Rate `4×0.75=3 req/min` negligible.
- **Verification:** `has==== false`, `Chapter count == Tamil`, all `finish:stop`, no `REPEAT` loops (as Day3 `viran_mindar 1482× Thirumoolattanam` fixed).

## 3. Runner Changes Required

- **Template split:** `periapuranam/templates/run_nayanar_template.py` currently single `run()` does `download → chunk → transcribe → story merge → single-call translate`. Must refactor to `def run_phase(nayanar, seq_fid, phase: A|B|C)` with `argparse --phase`. Keep shared `slugify`, `headers`, `download_drive` (with `120s 3×`), `get_duration`, `make_chunk`, `transcribe_chunk`, `translate_chunk`, `instrumentation`. Or keep template as reference and generate 3 per-slug wrappers: `run_<slug>_phaseA.py` etc. — but per instructions `Python Runner Naming Convention periapuranam/run_<full_nayanar_slug>.py` mandatory, so Phase flag inside single runner is cleaner: `run_<slug>.py --phase A` default `A+B+C` for compatibility, but batch wrappers call explicit phase.
- **Batch wrappers:** New `periapuranam/run_day07_phaseA.py` (downloads 2-parallel), `run_day07_phaseB.py` (transcribe 4-parallel, `POLL 30s HEARTBEAT 300s` `python -u`), `run_day07_phaseC.py` (translate 4-parallel chunked). Reuse `periapuranam/run_day06_batch_2parallel.py:12` meter logic but with `max_workers=4` for B/C.
- **Day06 retrofit:** `chandesura/karaikal` runners still contain single-call translate — should be disabled for Day07+ (comment out or guard `if phase in (C, all)`). Existing `run_day06_batch_2parallel.py` and `run_day06_translate.py` already separate B/C — keep as reference for new phase wrappers.
- **Cost logging:** Phase A no cost, Phase B `transcribe_log.json` + `instrumentation.json` `cost per chunk`, Phase C `english_real/*_meta.json` `cost per chunk` + `*_english_meta.json` aggregated.

## 4. Parallel Feasibility (post-download)

- **Phase A:** Recommend `2-parallel` (proven) `30s stagger`, `120s timeout 3×`. `4-parallel` still risky (Drive `Read timed out` + `160K Invalid data` at 6.5m). If we need 4, increase stagger to `60s` and timeout `180s`, but 2 is safest for 96F Day06/07.
- **Phase B:** Recommend `4-parallel` (no host). Math: `336ch 22s avg → 123m seq → 31m 4-worker + stagger 1.5m =32m` vs `61m 2-worker`. Rate `10 req/min <20`. Already validated `3-parallel 38m 120ch 0 anomalies` Day05; `2-parallel 130ch 40.5m` Day06. 4 should work — monitor `ConnectionReset 10054` (transient, retry ok) and `Budget 402` fail-fast `exit2`.
- **Phase C:** Recommend `4-parallel` as well. `65 stories 408 files` small batch English `~2h seq 65×100s` → `30m 4-worker`. Day06 `8 chunks 267s avg 9.6m 2× sequential → 4.8m 4-worker`. No host, only `≤4 req/min`.

**Execution order tomorrow (Day07 example: 2×36F Sundarar deferred? or next Day06 remaining):**
1. `python -u periapuranam/run_day07_phaseA.py` → verify `audio/*.mp3` `18/28/32` `ffprobe` `>1M`.
2. `python -u periapuranam/run_day07_phaseB.py` (4-parallel) → verify `Chapter N==files` `no ====`.
3. Manual fix pass for `HUGE/TINY/EMPTY` (as Day06 246/493) → re-merge.
4. `python -u periapuranam/run_day07_phaseC.py` (4-parallel chunked `60K`) → verify `finish:stop`.

## 5. Tracker Updates

- `periapuranam/day_wise_plan.xlsx` `Day 6` rows `chandesura 18/18 66ch 0.575+0.137=0.712`, `karaikal 18/18 64ch 0.499+0.130=0.630` `Status Done Human Verified No` `periapuranam/day_wise_plan.xlsx:Day 6`.
- `DayWise_Plan` Day6 `36/96 130/336 50m wall 1.34$ Partial`.

## 6. Decisions (2026-09-16)

- **Phase A:** `2-parallel` (confirmed).
- **Runner:** single `periapuranam/run_<slug>.py --phase A|B|C` (confirmed, keeps `process_instructions.md:9` naming).
- **Tails `251c03 75s 0` `261c04 34s 0`:** `0 len cost None finish:stop` on 2× retry → not re-transcribed, **write error log and pause for manual review** (as `instrumentation.json` `EMPTY_0CHAR`). Review `tamil_real/*_chunk*.txt` + listen `±1` audio per `process_instructions.md:33` before Phase C. Keep `0` as valid silence but flagged, do not auto-advance.
- **Day07 scope:** remaining `kazharitrarivar 28F (937-964) + kannappa 32F (124-155)` `60F 210ch` first; `Sundarar 36F` deferred per `Day 7` plan.

## 7. Phase Gate & Error Log

- After Phase B, `*_instrumentation.json` `anomalies` non-empty → write `periapuranam/output/<DAY>/<slug>/tamil_real/<slug>_errors.log` (per-chunk `flag`, `chars`, `cost`, `finish`, `duration_chunk_s`) and **pause batch** — do not start Phase C until human clears `anomalies` (re-transcribe or accept silence). Example Day06: `246 HUGE` fixed by deleting `395B` mp3, `493 TINY` re-transcribed `22→3438`, `251/261 EMPTY` logged as `tail silence` for review.
- Batch wrappers `run_dayXX_phaseB.py` exit `1` if `anomalies` remain, to enforce `Stop-and-Review Gate` `process_instructions.md:33`.
