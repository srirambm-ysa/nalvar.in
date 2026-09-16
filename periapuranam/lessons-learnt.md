# Periapuranam Nayanar Build — Lessons Learnt (Day 1-5)

> Living document. Updated after each Day. Used to keep scaling to larger stories (18–36 files, giants 62–291) reliable. See `docs/process_instructions.md` + `docs/download_strategy.md`.

## 1. Two-Pass Pipeline (Transcribe → Verify → Translate → Verify)

**Why:** Single-pass (transcribe+translate in one runner) mixes progress meters, hides Tamil failures until English truncates, and wastes cost. Day 5 `095 HUGE 43k` + English `30000 max_tokens` truncation (`amar 137K Tamil → 30000 completion length`) proved it.

**Now:**
- **Pass 1 — Tamil only:** `run_<slug>.py` until `tamil_real/<slug>_tamil.txt` + `transcribe_log.json` + `instrumentation.json`. Stop. Verify `no ====`, `Chapter N==files`, `finish stop`, dur-aware anomalies.
- **Pass 2 — English only:** Separate callable `periapuranam/run_day05_translate.py` (not batched in transcribe). Tamil `*_tamil.txt` already verified → chunked translate into `english_real/<slug>_english_chunk*.txt` + `*_instrumentation.json` → merge `*_english.txt` + `*_bilingual.txt`. Meter reset `1/3 stories`.

**Rule:** Never batch translate in transcribe run for `≥50K Tamil` (Day5 11-13 files). Giants (`Yeyar 62, Thirunavukkarasu 215, Sambandha 291`) will always be chunked.

## 2. Chunking & Limits

### Tamil audio chunking
- `ffmpeg -ss offset -i mp3 -t 300 -c:a libmp3lame -b:a 64k` → `~110KB/300s`, `~1s/chunk`. Verified `14-18 MB` per file, `3-5 chunks` avg.
- **Trap:** Offset `900s` for `914s` file failed when audio truncated at `800s` (14M→13M incomplete download). ffprobe `duration 914` still reported, but `ffmpeg -ss 900` produced `395B` invalid. Flag: chunk `<1000` bytes + `ffprobe Invalid`.
- **Fix:** Re-download `GET https://drive.usercontent.google.com/download?id={fid}` with confirm token if `chunk mp3 <1KB` or `ffprobe Invalid`. Check `ffprobe stream duration` vs `format duration`.

### English translation chunking
- Single call `max_tokens 30000` sufficient for `<70K Tamil` (~20K tokens completion). For `≥100K Tamil` (Day5 13-file `137-152K chars`) hits `finish length` truncation.
- **Chunk by Chapters:** `chunk_tamil_by_chapters(story, limit 60000)` → groups `~45-60K` Tamil → `2-3` LLM calls (`temperature 0.4`, `max_tokens 30000`). Preserves `Chapter 01` headings via `(?=^Chapter \d{2} —)` regex. Stored `english_real/<slug>_english_chunk00.txt` + `*_meta.json` for audit. Merge `"\n\n"` in order.
- Idempotent resume: skip chunk if `*_english_chunk*.txt >500` + `meta finish stop` + `>1000 chars`.

## 3. Anomaly Detection (Dur-Aware)

- **Not raw `<1K`:** Many `<1K` chunks are legit tails (`dur 3-77s`, `min_expected = max(30, dur*6)`). Day5 tails `092 ch3 41s 449c` pass.
- **Flags only:**
  - `EMPTY_0CHAR` (`chars==0`)
  - `TINY_{chars}_dur{dur}_exp{min}` if `chars < dur*6`
  - `HUGE_{chars}_dur{dur}_exp{max}` if `chars > dur*20+500`
  - `REPEAT_{8char window}>30` for loops (e.g. `095 ch3 43k dot repeat`)
- Verified Day5: only 4 true failures of 149 chunks (`095 HUGE`, `111 TINY 7`, `926 TINY 7`, `928 EMPTY`). All re-transcribed single-chunk `temperature 0.1` with valid `110KB` audio → `89-544c` correct. Other `<1K` left alone.
- Instrumentation: `tamil_real/*_instrumentation.json` per-chunk `chars, flag, dur_chunk_s, dur_transcribe_s, cost, finish, prompt_tokens`. Retain for audit; do not rely on raw `ls -lh`.

## 4. Progress Meter & Instrumentation

- **Old:** `POLL 5s` log parsing `count_progress()` → `0/136` spam for 11 mins (buffered `print` not flushed, log empty until process end).
- **New:**
  - `python -u` + `PYTHONUNBUFFERED=1` + `print(..., flush=True)` for unbuffered logs.
  - Filesystem truth: count `periyapuranam-*_chunk*.txt >500 && "[FAILED" not in` not log regex.
  - Event-based: print only when `done_total != last_done` or `heartbeat 300s` (5-min). `POLL 30s` internal.
  - Separate meters: Tamil `X/149` chunks, English `X/3 stories` + `X/3 chunks` inside story (`1/3 Chapter 01-04 → 58857c`).
  - `batch_progress.json` written every poll for resume/dashboard, but console quiet.

## 5. Resume & Idempotency

- **Tamil chunk resume:** Before `transcribe_chunk`, check `tamil_real/periyapuranam-XXX_chunkYY.txt >500 && "[FAILED" not in && len>30` → `print cached ... skip API` + `continue`. Saves `$0.36` for 38 cached chunks on Day5 restart (12:21 `RESUME 38/136`).
- **English chunk resume:** Same for `english_real/*_english_chunk*.txt` + `*_meta.json finish stop`.
- **Audio resume:** `audio/periyapuranam-XXX-{fid}.mp3 >1M` skip download. Verify size via `ls -lh`; if `ffprobe Invalid` → re-download.

## 6. Budget & Rate Limit

- `402/403 Budget/insufficient` → `sys.exit(2)` fail-fast, no 3× retry loop (was wasting `18s` per failed chunk at 15→30 limit). Added to `templates/run_nayanar_template.py:149` + 60 runners.
- Throttle `2.0s` between chunks + `30s stagger` for 3-parallel (`≤20 req/min`). Day5 3-parallel `120ch 38m wall` vs `120m seq` (`2.0s` safe for OpenRouter `google/gemini-2.5-flash $0.30/1M prompt, $1.00/1M audio, $2.50/1M completion`).
- Stagger prevents burst `3×` at start.

## 7. Cost & Scale Estimates (measured)

| Day | Files | Chunks | Tamil | English | Total | Wall 3-parallel |
|-----|-------|--------|-------|---------|-------|----------------|
| Day1 21×1 |21|74| $0.76| $0.20| $0.96| 86ch |
| Day2 14×2/3 |34|123| $1.05| $0.29| $1.35| - |
| Day3 11×4-6 |56|217| $1.80| $0.50| $2.30| - |
| Day4 7×7-9 |56|223| $1.66| $0.46| $2.31| 28m 2-workers |
| Day5 6×11-13 |73|269| $1.92| $0.53| $2.42| 38m+10m chunked |
| Day6 plan 4×18-32 |96|336| — | — | $3.24| ~45m chunked |

- Small batch `408F 1428ch` → Day1-5 `201F` done, Day6 `96F` remains. Giants `568F` deferred `Day11+`.

## 8. Verification Checklist (before next Day)

- [ ] `grep -c ==== *_tamil.txt` `==0` and `*_english.txt` `==0`
- [ ] `grep -c "^Chapter "` equals `files` (e.g. `Chapter 13/13`)
- [ ] `finish_reason stop` in `english_real/*_meta.json` and `tamil instrumentation`
- [ ] `anomalies ==0` in `*_instrumentation.json` (or fixed and re-merged)
- [ ] Spot-listen `±1` audio per story for drift (`pilot revealed synthetic drift`)
- [ ] `transcribe_log.json` + `english_meta.json` costs logged
- [ ] `output/day-0X/` size + file counts match `day_wise_plan.xlsx`

## 9. Scaling to Giants (Day6-10, 11+)

- **Day6** `Chandesura 18F, Karaikal 18F, Kazharitrarivar 28F, Kannappa 32F` → same two-pass, but `english_real` will be 3-4 chunks per story (Kannappa `32F ~120ch ~400K Tamil` → 6-7 English chunks). Use `CHUNK_TAMIL_LIMIT 55000` for them.
- **Giants** `Yeyar 62, Thirunavukkarasu 215, Sambandha 291` → Tamil already `4-worker` `13.8h seq / 3.5h wall`, English needs `2-3 chunked calls` each (`Sambandha 291F 3.2M chars 1.1M tokens $3.42` context 1M). Must chunk Tamil story itself for translate (not just audio).
- **Reversibility:** delete `periapuranam/output/day-0X/<slug>/` to revert Nayanar; delete `day-0X/` for whole day; `discarded/` holds zipped `parasakthi` never deployed.

## 10. Open Issues / Next

- Update runners to auto-chunk English when `story_chars >60000` (template currently single-call).
- Automate `ffprobe Invalid` → re-download in `download_drive`.
- Final `Day 1-4 Human Verified No→Yes` after spot-listen.

*Last updated: 2026-09-16 Day5 6/6 Done.*
