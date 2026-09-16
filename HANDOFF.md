# HANDOFF — Nalvar (D:\nalvar)

> **Purpose:** project-local detailed handoff for continued work on `nalvar.in` — PWA, SEO, path routing, and Blog phase 2. The wiki `D:\knowledge-base\HANDOFF.md` is the thin master pointer; this file is the **authoritative project detail**.
>
> **Last updated:** 2026-09-16 · `main` at `e83750d` (Day6 2/4 DONE Chandesura 18F 66ch 206K + Karaikal 18F 64ch 198K 2-parallel 40.5m + 9.6m chunked English — 246 HUGE 37k/50k fixed 255K→5827, 493 TINY 22→3438, 251/261 tails 0 flagged) · `output/day-06` 2/4 done 36F 130ch $1.34 — `output/day-01` 21 + `day-02` 14 + `day-03` 11 + `day-04` 7 + `day-05` 6 + `day-06` 2/4 = 61/71 total stories, 250 files · Strategy `periapuranam/transcription-strategy.md` 3-phase A/B/C created → Day6 remaining 60F Kazhar/Kannappa queued Phase A 2-parallel

> **Stack:** static PWA (no framework), `index.html` + `data.json` + `remedies.json` + `blog/` + `periapuranam/` (catalog 1024 + Nayanar build day-batched `output/day-01`, `day-02`), Cloudflare Workers Assets (`wrangler.toml` `directory ./dist` `not_found_handling single-page-application`), `sw.js` precache, `manifest.webmanifest`, `scripts/admin-dev-server.mjs` inline PUT dev server

---

## 1. Goal Accomplished — This Session (2026-09-16 · Day6 2/4 Chandesura+Karaikal 36F + 3-Phase Strategy)

- **Day6 Phase A+B 2/4 DONE via 2-parallel (40.5m wall) + Phase C chunked English (9.6m) — output/day-06 2 folders 36F 130ch $1.34 (Tamil $1.07 + English $0.27):** `Chandesura 245-262 18F 66ch 206153c 566KB $0.575T+0.137E=0.712` (`246 HUGE 37492/50799 finish:length` from `395B empty mp3` header `1064s vs valid 510s` → deleted `104K/139K` + `246_chunk02/03_600s 395B`, re-merged `255K→5827` 2 chunks), `Karaikal 486-503 18F 64ch 198444c 543KB $0.499+0.130=0.630` (`493c01 22 TINY→3438` re-transcribed `ConnectionReset 10054` retry, re-merged `6124→9540`) — both `18 Chapters no ==== finish:stop` `bilingual 773K/736K`. Tails `251c03 75s 0` `261c04 34s 0` consistently `0 len cost None` on retry → logged `EMPTY_0CHAR` as tail silence, kept flagged for manual review per Q3. **Host fix:** `templates/run_nayanar_template.py:28` `download_drive 60→120s 3× retry backoff 5*try >1M` (4-parallel `Read timed out` + `kazhar 160K Invalid` fixed, 2-parallel stable). **Batch:** `run_day06_batch_2parallel.py:12` `2-parallel 30s stagger POLL 30s HEARTBEAT 300s python -u filesystem count` `36F 130ch 40.5m` vs `96F 336ch 123m seq`; `run_day06_translate.py` chunked `60K` `4×4` `80s avg` `9.6m`.
- **Phase separation validated:** 4-parallel download failed at `6.5m` (`kazhar 937 160K`, `chandesura 246 Read timed out`, `karaikal 10054`), 2-parallel succeeded `7/126→127/126`. Manual `curl 120s` solo succeeded, confirming host concurrent limit. Post-download Phase B/C can be 4-parallel (no host) — `10 req/min <20` `periapuranam/transcription-strategy.md:4`.
- **3-phase strategy from Day07:** `periapuranam/transcription-strategy.md:1` created (7 sections: Why 3 Phases, Phase A/B/C definitions, Runner Changes, Parallel Feasibility, Execution Order, Tracker, Decisions). Decisions: Phase A `2-parallel` (Q1), single runner `run_<slug>.py --phase A|B|C` (Q2, keeps `process_instructions.md:9` naming), tails `0` → **write `tamil_real/<slug>_errors.log` and pause batch** for manual review (Q3, `transcription-strategy.md:7` gate).
- **Runner template refactor:** `periapuranam/templates/run_nayanar_template.py:11` `run(nayanar, seq_fid, phase=all)` `PHASES A/B/C` `periapuranam/templates/run_nayanar_template.py:12` + `Phase A download-only` `Phase B chunk+transcribe+story merge+instrumentation+_errors.log pause` `Phase C chunked 60K english_real` `re` import `periapuranam/templates/run_nayanar_template.py:236` replaces single-call `30000` truncated `138K length`. Regenerated `run_chandesura/karaikal/kazhar/kannappa_nayanar.py` `DAY day-06` with phase support.
- **Tracker:** `periapuranam/day_wise_plan.xlsx:Day 6` `chandesura 18/18 66ch 0.575/0.137 Done` `karaikal 18/18 64ch 0.499/0.130 Done` `DayWise_Plan Day6 36/96 130/336 50m wall 1.34$ Partial` `periapuranam/day_wise_plan.xlsx:7`.


## 1. Goal Accomplished — Prior Session (2026-09-16 · Day5 6/6 Two-Pass Complete + Chunked English + Lessons)

- **Day5 6/6 DONE two-pass 73F 269ch $2.42 — output/day-05 6 folders:** `Murthi 11F 43ch 353K Tamil 125K English $0.436`, `Tiruneelanakkar 11F 35ch 275K 99K $0.345`, `Appoothi 12F 42ch 355K 120K $0.432` (3-parallel `38m wall 2.0s throttle 30s stagger`) + **Pass1 Tamil fix + Pass2 English chunked 39F 149ch:** `Amar-Niti 13F 48ch 376K Tamil 132K English $0.365` (`095 HUGE 43198→176c` after re-download 13M→14.2M + chunk `0.4K→110K` valid, `39747` repeat fixed), `Eri-Pattha 13F 53ch 417K 155K $0.438` (`111 TINY 7→81c`), `Siruthonda 13F 48ch 410K 142K $0.401` (`926 TINY 7→89c`, `928 EMPTY 0→544c`) — all `no ====`, `Chapter 11/11/12 13/13/13 ==files`, `finish stop`, `bilingual 508-573K`. **Meter fixed:** `run_day05_batch.py:15` `POLL 30s + HEARTBEAT 300s` filesystem count `RESUME 38/136` event-based, `python -u` unbuffered; **English separate:** `run_day05_translate.py:1` `english_real/` `CHUNK_TAMIL_LIMIT 60000` `3 chunks` per story `Chapter 01-04,05-09,10-13` `stop` no truncation (was `30000 max` length).
- **Two-pass now mandatory:** `Transcribe → Verify (anomalies dur-aware min dur*6 / max dur*20+500, ffprobe Invalid → re-download) → Translate chunked → Verify` per `periapuranam/lessons-learnt.md:1`. Added `run_amar/eri/siruthonda_nayanar.py:309` cached skip `>500 && not FAILED` (saves $0.36 for 38 cached chunks on resume).
- **Tracker updated:** `periapuranam/day_wise_plan.xlsx:DayWise_Plan` `J6 2026-09-16 K6 73/73 L6 269ch 52m wall M6 2.4193 O6 Done` + `Day 5` rows `Amar 48ch $0.274+0.090=0.365, Eri 53ch $0.333+0.105=0.438, Siru 48ch $0.304+0.096=0.401` all `Done`.
- **Lessons:** `periapuranam/lessons-learnt.md:1` created (10 sections: two-pass, chunking 300s/60K, dur-aware flags, meter unbuffered, resume skip, budget fail-fast, cost $2.42 Day5, verification checklist, scaling to Day6 96F 336ch + giants 568F).

## 1. Goal Accomplished — Prior Session (2026-09-15 cont · Day5 3/6 3-Parallel + Budget Fix + Wrapper)

- **Day5 3/6 DONE via 3-parallel (38m wall 18:07-18:45, throttle 2.0s +30s stagger) — output/day-05 34F 120ch:** `Murthi 180-190 11F 43ch 129072c $0.084 353718b 0 anomalies 2103s`, `Tiruneelanakkar 516-526 11F 35ch 100064c $0.067 275373b 0 anomalies after fix 1799s` (was `524 chunk03 30s 0c EMPTY` → re-transcribed `397c $0.00107` + re-merged `10769c` + re-translated `99495c`), `Appoothi 504-515 12F 42ch 129395c $0.084 355322b 0 anomalies 2038s` — all `no ====`, `Chapter 11/11/12 ==files`, `finish:stop`, `bilingual 254k/196k/249k`. **120ch wall 38m** vs `120m seq`, `Day5 73F 256ch` half done, remaining `Amar 91-103 13F 45ch + Eri 105-117 13F 45ch + Siruthonda 924-936 13F 46ch =39F 136ch` queued.
- **Budget fail-fast patched:** `periapuranam/templates/run_nayanar_template.py:149` + `60 run_*.py` now detect `402/403 Budget/insufficient` → `print FATAL BUDGET ... sys.exit(2)` instead of `3× retry → [FAILED TRANSCRIPTION] 22c` loop (was wasting `18s` per failed chunk at `murthi 180 2 ok +10 failed` + producing `periyapuranam-181-tamil-real.txt 94c` etc.). Tested `curl key` limit `15→30` `remaining 6.33` after credit add; `hello` now `200`.
- **Resume skip added for recovery:** `run_murthi/tiruneelanakkar/appoothi` now check `periyapuranam-XXX_chunkYY.txt >500 && not FAILED` → `cached X chars skip API` (saves re-pay on budget abort), then clean restart after fix retained audio `14-21MB` only, deleted `tamil_real/*.txt` `22c` failures.
- **Progress wrapper prepared:** `periapuranam/run_day05_batch.py:1` launches `3` as `subprocess.Popen` with `30s` stagger, polls `logs/*.log` every `5s` for `cached/ cost` + `expected 45/45/46`, prints `[wall 5.2m] 47/136 35% $1.20 ETA 18m | amar 11/45 run ...` + `output/day-05/batch_progress.json` for meter, wall tracking `wall_s/wall_m`. Will run remaining 3 next session (not now).
- **Tracker fix earlier:** `periapuranam/day_wise_plan.xlsx:DayWise_Plan` `I5 $1.88 J5 2026-09-15 K5 56/56 L5 223ch M5 2.3147 O5 Done` + `J2/K2/L2/M2/O2` `21/21 86ch $0.964 Done` + `J3/K3/L3/M3/O3` `14/14 123ch $1.355 Done`.

## 1. Goal Accomplished — Prior Session (2026-09-15 · Day4 7/7 Complete + Dur-Aware + Day5 Prep)

- **Anaya promoted:** `periapuranam/_test_merge/anaya_nayanar/` `106M` `64845c 6 Chapter` `66881c Eng $0.045` → `periapuranam/output/day-04/anaya_nayanar/` `7 MP3` `25 chunks` `periyapuranam-173..179-tamil-real.txt` + `anaya_nayanar_tamil.txt` `177KB` `anaya_nayanar_english.txt` `67KB` `anaya_nayanar_bilingual.txt` `244K` ` periyapuranam/run_anaya_nayanar.py` `DAY day-04` (promoted early per owner, `_test_merge/` deleted).
- **Day4 7/7 DONE via 2-workers parallel + dur-aware instrumentation — output/day-04 7 folders 56 files 223 chunks $2.12 (Tamil $1.66 + Eng $0.46) — verified `no ====`, `Chapter N==files` `finish:stop`:** `Mei-p-porul 78-84 7F 28ch $0.238+0.058 89655c→86165c` (fixed `083_chunk02 0c→3474c 12.6s`), `Sakkiya 915-922 8F 38ch 120294c chunked translate 63k+57k $0.082 82s+85s`, `ThiruMoola 900-907 8F 32ch 105748c $0.080 0 anomalies`, `Tirunilakanta 55-62 8F 32ch 97067c 0 anomalies`, `IyarPakai 63-71 9F 35ch 99553c HUGE 064 22k→3493c fixed $0.066`, `TirunAlaippOvAr 200-208 9F 33ch 96786c 0 anomalies` = **673948c Tamil** `389 files  ~1.1GB` on disk, `~28m` wall `2 workers` vs `~48m seq` (`Day 4:1h22m` plan). Thresholds `min dur*6/max dur*20+500` eliminated false `TINY_17/142/160/254`, correctly flagged `HUGE 22k` + `EMPTY 0c`.
- **Template patch:** `periapuranam/templates/run_nayanar_template.py:2` `+73` `datetime/collections` `INSTRUMENT/ANOMALIES` `dur-aware _flag_anomaly` `t0/dur_t` `if not content.strip()` `instrumentation.json` dump before translate — future Day5+ safe to `80K` Tamil (`30000` max_tokens already Day3). Also applied to all `run_mei/sakkiya/thirumoola/...` runners.
- **Day5 prep 6/6 runners ready DAY day-05:** `Murthi 180-190 11F 38.5ch`, `Tiruneelanakkar 516-526 11F`, `Appoothi 504-515 12F 42ch`, `Amar-Niti 91-103 13F 45.5ch`, `Eri-Pattha 105-117 13F`, `Siruthonda 924-936 13F 45.5ch` = **73F 256ch est $2.45 1h47m seq / ~25m 2-workers** (from `templates/run_nayanar_template.py:11` `DAY day-05` + `DEFAULT_SEQ_FID` per `Day 5` sheet).
- **Tracker:** `periapuranam/day_wise_plan.xlsx:Day 4` all 7 rows `Done / Actual Files/Chunks / Tamil/English/Total Cost / Human Verified Yes / Retries` + `DayWise_Plan` row4 `2026-09-15 56/56 223ch $2.12 Done` + `Anomalies` still `Poyyadiai WRONG, KazharChinga 41832, Thillai 0-char` deferred.
- **Selective backup `f76d523`:** `36 files` `periapuranam/day_wise_plan.xlsx` + `templates/run_nayanar_template.py` + `13 run_*.py` (Anaya + 6 Day4 + 6 Day5) + `21 final txt` `day-04/*/tamil_real/*_tamil.txt + /*_english.txt + /*_bilingual.txt` (ignore `audio/` `*_chunk*.txt` per `.gitignore`), pushed `main f76d523`.

## 1. Goal Accomplished — Prior Session (2026-09-14 · Day3 11/11 Complete + Viran Mindar Fix)

- **Day3 11/11 DONE — output/day-03 11 folders 56 files 217 chunks $2.3045 (Tamil $1.8036 + English $0.5009) — verified `no ====`, `Chapter 04/05/06` + `finish:stop`:** `Muruga 191-194 4f 16ch $0.1522 44694c` + `Muzhu 1005-1008 4f 15ch $0.1668 50653c` + `Pugazh 968-971 4f 14ch $0.1360 41532c` + `Chithaththaich 996-1000 5f 20ch $0.2264 65514c` + `Dhandi 908-912 5f 24ch $0.2760 80590c` + `Perumizhala 481-485 5f 18ch $0.1994 58220c (resumed 483 partial + 1 retry 10054)` + `Rudhra 195-199 5f 18ch $0.1733 49083c` + `Eanati 118-123 6f 24ch $0.2501 71655c` + `Manakkanchara 164-169 6f 22ch $0.2397 67618c` + `Mara 72-77 6f 24ch $0.2432 72124c` + `Viran Mindar 85-90 6f 22ch $0.2416 62406c **FIXED**` = **751.8 MB 384 files** (`tamil_real/*_tamil.txt` + `*_english.txt` + `*_bilingual.txt` each). Plan `56f 196ch $1.89` vs actual `56f 217ch $2.30` (21 extra chunks due to longer audio avg 962s).
- **Viran Mindar anomaly fixed 2026-09-14:** English Chapter 05 loop `1482× "Thirumoolattanam"` / `1479× "in Thirumoolattanam,"` (42,594 chars) + stray `Chapter 8, Religion...` 1,111 chars between Ch02→Ch03 (total 94,947). Tamil Ch05 `11,483` correct. Re-translated Ch05 alone `temp 0.3 15k` → `11,573` clean `1× Thirumoolattanam` cost `0.00757`, removed stray block, rebuilt `viran_mindar_nayanar_english.txt 62,819` + `_bilingual.txt 234,598` + `_english_meta_fix.json`. New headers `01..06` only, `no ====`, `bilingual 12ch`.
- **Tracker updated:** `periapuranam/day_wise_plan.xlsx:Day 3` all 11 rows `Status Done / Actual Files/Chunks / Tamil/English/Total Cost / Human Verified No / Retries / Comments` filled + `DayWise_Plan` row3 `2026-09-14 56/56 $2.30449 Done` + `Anomalies` row5 Viran FIXED (kept for final review, green). Existing anomalies `KazharChinga 41832`, `Thillai 0-char`, `Poyyadiai WRONG` remain OPEN deferred to batch anomaly day per owner.

## 1. Goal Accomplished — Prior Session (2026-09-10 · Day3 5/11 + Translation Truncation Fix)

- **Day3 5/11 stories done (40 files, 79 chunks) — output/day-03 5 folders, verified stop/finish no length:** `Muruga 191-194 4ch 16ch $0.1522` + `Muzhu Neeru 1005-1008 4ch 15ch $0.1668` + `Pugazh Chozha 968-971 4ch 14ch $0.1360` + `Chithaththaich 996-1000 5ch 20ch $0.2264` + `Dhandi 908-912 5ch 24ch $0.2802 (Tamil $0.2188 + English $0.0614 after fix)` = **Tamil $0.7313 + English $0.2303 = $0.9616** for 5 stories (plan $0.93 for 4-5 file avg). Each `output/day-03/<slug>/` `audio/*.mp3` + `tamil_real/*-tamil-real.txt` + `*_chunk*.txt` + `<slug>_tamil.txt` (Chapter 04/05, 41-80KB, no ====) + `<slug>_english.txt` + `_meta.json` + `_bilingual.txt`. Headers pass `^Chapter \d+` (4/5), no ====.
- **Translation truncation root cause fixed:** Single-call `max_tokens 12000` truncated every story >40K Tamil chars — verified `muruga 4ch 44694 finish:length 11999` tail cut “Only those who had performed”, `muzhu 50653 length 12000`, `chithaththaich 65514 5ch but Eng 4ch`, `dhandi 80590 5ch but Eng 3ch`. Live probe `25000` fixes muruga `stop 11855 49473`, `30000` fixes all: `muzhu stop 13228 54429`, `chithaththaich stop 17431 74889`, `dhandi stop 20657 81271` then `retranslate_day3.py` rewrote 4× `*_english.txt` + `*_bilingual.txt` with `30000` (final muruga `12183 49473 stop`, muzhu `13442 54429 stop`, chithaththaich `17616 74889 stop`, dhandi `22154 88826 stop`). **Template fix:** `templates/run_nayanar_template.py:154` `payload_en 12000→30000` + all `run_*.py` patched (46 files) — future Day3/Day4+ safe to 80K Tamil.
- **Day3 runners created:** 11× `run_<slug>.py` DAY `day-03` from `templates/run_nayanar_template.py:11` + `DEFAULT_SEQ_FID` per `Day 3` sheet: `muruga_nayanar 191-194`, `muzhu_neeru_poosiya_munivar 1005-1008`, `pugazh_chozha_nayanar 968-971`, `chithaththaich_sivan_pale_vaiththar 996-1000`, `dhandi_adigal_nayanar 908-912`, `perumizhalaikurumba_nayanar 481-485`, `rudhra_pasupadhi_nayanar 195-199`, `eanati_nathar_nayanar 118-123`, `manakkanchara_nayanar 164-169`, `mara_nayanar 72-77`, `viran_mindar_nayanar 85-90`. First batch 5 ran 18:02-18:43 `1h` (network drop at 18:43 caused `EN length` + `DNS drive.usercontent` for remaining 6) — network recovered 18:50, fix applied, then paused per owner.
- **Pending Day3 6/11 not started due to network drop + owner pause:** `perumizhalaikurumba_nayanar 5 files`, `rudhra_pasupadhi_nayanar 5`, `eanati_nathar_nayanar 6`, `manakkanchara_nayanar 6`, `mara_nayanar 6`, `viran_mindar_nayanar 6` = **34 files ~122 chunks est $1.18** remain. Idempotent rerun will skip downloaded `audio/*.mp3` and reuse `tamil_real` chunks. Anomalies `KazharChinga 987 halluc 41832` + `Thillai 053 0-char` still deferred to batch anomaly day per owner.
- **Session token count (2026-09-10 Day3):** REAL billed **1,418,301** (RAW 9,371,266, **84.9% caching**, **94.7% hit**, **84 req**) — 11 runners created + 5× transcribe/translate + 4× retranslate 30000 + truncation audit.

## 1. Goal Accomplished — Prior Session (2026-09-10 · Day2 Nayanar Build 14/14 + Anomalies Tab + Selective Backup)

- **Day2 14 stories sequential complete — output/day-02 14 folders 397 MB, 123 chunks $1.3558 (plan $1.15):** `AdhiBaththa 973,974 dup 8ch $0.0886` + `Bakthraaip 993,994 6ch $0.0608` + `Idangazhi 988,989 7ch $0.0718` + `Isaignani 1021,1022 7ch $0.0678` + `Kaari 982,983 9ch $0.0945` + `KanamPulla 980,981 6ch $0.0660` + `KazharChinga 986,987 7ch $0.1154 **flagged 41832 hallucination**` + `Poosalaar 1010,1011 7ch $0.0815` + `Thillai Vazh 52,53,54 9ch $0.0938 **flagged 0-char chunk**` + `Arivattaya 170,171,172 13ch $0.1426` + `Kulacchirai 478,479,480 10ch $0.1111` + `Muppodhum 1002,1003,1004 12ch $0.1243` + `Kochengat 1014,1015,1016 12ch $0.1263` + `ThiruNeelaKanta 1017,1018,1019 10ch $0.1115` = **Tamil $1.0589 + English $0.2969 = $1.3558**, `Chapter 02/03` headers pass, `no ====`, bilingual `Chapter*2`. Each `output/day-02/<slug>/` `audio/*.mp3` (excluded) + `tamil_real/*-tamil-real.txt` + `*_chunk*.txt` (ignored) + `<slug>_tamil.txt` + `<slug>_english.txt` + `_bilingual.txt` (committed). 14 runners `run_<slug>.py` DAY `day-02` from `templates/run_nayanar_template.py:11`.
- **Poyyadiai flagged after review:** `periapuranam/output/day-01/poyyadiai_illadha_nayanar/` confirmed `WRONG` — English ends *“Thus, the seventh chapter ... Varkonda ... concludes. Now, we shall proceed to contemplate the eighth chapter, Poyyadimai Illadha...”* (Kootruva conclusion, not Poyyadiai). Updated `DUPLICATE_NOTE.txt` → flagged, added `FLAGGED_WRONG_CONTENT.txt`, tracker `Day 1 row16 Human Verified No — FLAGGED` + `DayWise_Plan Day1 notes` + `Anomalies` tab row1.
- **Anomalies tab created in `periapuranam/day_wise_plan.xlsx:Anomalies` (active, landscape, filter, 4 rows):** `DayWise_Plan, Anomalies, Instructions, Day1..Day10` order. Rows: `Poyyadiai Day1 WRONG duplicate fid — awaiting source` + `KazharChinga Day2 41832 hallucination — re-transcribe chunk01` + `Thillai Vazh Day2 0-char chunk53 — re-transcribe` + `AdhiBaththa Day2 INFO duplicate fid 973,974 same audio`. Columns `# Date/Day/Nayanar/Seq/Fid/Slug/Output Path/Anomaly Type/Description/Recommended Action/Status` styled (red OPEN, yellow INFO).
- **Selective backup committed `b7ec916`:** `35 runners + day_wise_plan.xlsx + 105 final txt` (`.gitignore` now `output/**/audio/` + `*_chunk*.txt`), 143 files, structure preserved `output/day-01` + `day-02`. Audio/chunk/meta excluded per request, no zip. Day1 `20/21 valid +1 flagged`, Day2 `14/14 done pending verify`. Wiki project `nalvar` card updated (`projects/apps/nalvar.md`), `project-abbrevs NV`, tasks `NV-TSK-0001/0002 done`.
- **Verification:** Day2 headers pass strict `^Chapter \d+` (`tHdr 2/3, eHdr 2/3, bHdr 4/6, no ====`) for all 14; costs logged `tamil_real/transcribe_log.json` + `*_english_meta.json`; disk `day-01 244 MB + day-02 397 MB = 629 MB 496 files`.
- **Session token count (2026-09-10):** REAL billed **2,989,614** (RAW 19,798,705, **84.9%** caching, **94.7%** hit, **160** req) — Day2 14 stories sequential + Anomalies tab + selective backup.

## 1. Goal Accomplished — Prior Session (2026-09-09 · Day1 Nayanar Build 21/21 + Hygiene)

- **Day1 21×1-file Nayanars complete — all transcribed + translated:** `Appalum AdiCharndhar 1009 862s 3ch $0.03657` + `Chadaiya 1020 630s 3ch $0.02084 (1 retry 10054)` + `GanaNadhar 965 1074s 4ch $0.04410` + `Kalikamba 975 1183s 4ch $0.04897` + `Kaliya 976 1414s 5ch $0.06001` + `Kootruva 966 1558s 6ch $0.06576` + `Kotpuli 992 1449s 5ch $0.06217` + `Mangaiyarkkarsi 1012 839s 3ch $0.03689` + `Moorkka 913 1506s 6ch $0.06351` + `Munaiyaduvar 985 970s 4ch $0.04168` + `Narasinga 972 1169s 4ch $0.04894` + `Nesa 1013 823s 3ch $0.03492` + `Paramanaiye Paduvar 995 677s 3ch $0.02918` + `Poyyadiai illadha 967 1558s 6ch $0.06568 (dup of Kootruva, re-used audio)` + `PugazhThunai 991 1190s 4ch $0.05182` + `Sakthi 977 1324s 5ch $0.05432` + `Seruthunai 990 812s 3ch $0.03467` + `Sirappuli 923 874s 3ch $0.03620` + `Somasi Mara 914 1241s 5ch $0.05344` + `Thiruvarurp Pirandhar 1001 539s 2ch $0.02347` + `Vayilar 984 1214s 5ch $0.05122` = **Tamil $0.759 + English $0.205 = $0.964** (plan $0.71, overrun due to longer audio avg 4.1ch/file). Each `periapuranam/output/<slug>/` `audio/*.mp3` + `tamil_real/*-tamil-real.txt` + `*_chunk*.txt` + `<slug>_tamil.txt` (Chapter 01, no ====, 7-19KB) + `<slug>_english.txt` + `_meta.json` + `_bilingual.txt`. No `====`/`PART` separators, Chapter count verified 1. `21` runners `periapuranam/run_<full_slug>.py` ✓ from `periapuranam/templates/run_nayanar_template.py`.
- **Hygiene:** `periapuranam/parasakthi/` (4081 files, 15.7 MB) zipped → `discarded/parasakthi.zip` `5.3 MB` and removed; blog `*.json` backups (`blog.full.json` etc.) + `10` py generators → `discarded/` (17 files); `blog-*.md` 4 files → `docs/`; `periapuranam/day_wise_plan.xlsx` `9.2K old` → `discarded/periapuranam_day_wise_plan_old.xlsx`, `docs/day_wise_plan.xlsx` `40K 12 sheets` copied to `periapuranam/day_wise_plan.xlsx` (live) and `docs/day_wise_plan_baselined.xlsx` (frozen) — `docs/day_wise_plan.xlsx` duplicate remains locked (identical to baselined); `Day4 Anaya` marked `Done` `6 files 25ch $0.24535` pilot remains in `_test_merge`; template moved `discarded/run_nayanar_generic_template.py` → `periapuranam/templates/run_nayanar_template.py`, `docs/process_instructions.md:1` documents full pipeline + naming convention.
- **Deploys:** `wrangler deploy af8e6a31` `107 files` (trimmed 11 blog posts provenance card, `share-row`, `_headers`) → `https://nalvar.srirambm.workers.dev` + `https://nalvar.in` verified `grep -c provenance 0`; `Day1` audio/transcription not deployed (local `output/` only).

## 1. Goal Accomplished — Prior (2026-09-08 cont. · Periya Puranam 601-1024 Complete + Audit)

- **Batches 601-1024 — all 424 seqs done (4,447s total):** `601-700:100ok` (`601-641:41ok` + `642-700:59ok 686.8s` after key limit `403` at `642` — credit reactivated `limit:20 remaining:4.99→4.36`), `701-800:100ok 1128.1s`, `801-900:100ok +1 skip duplicate 1202.1s` (catalog `898` dup), `901-1000:100ok 1165.3s`, `1001-1024:24ok 289.9s`. Zero `fail` beyond the transient 403. Logs `batch_601-700.log` (incomplete split) + `batch_642-700.log` + `batch_701-800.log` + `batch_801-900.log` + `batch_901-1000.log` + `batch_1001-1024.log`; key usage `daily:1.988 remaining:4.364`.
- **Total corpus:** `periapuranam-*-tamil.txt:1014` / `english.txt:1014` / `bilingual.txt:1014` / `meta.json:1014` = **4056 files, 14MB** in `D:\nalvar\periapuranam\parasakthi\`. Corresponds to all catalog seqs except gap.
- **Audit 1-1024 (python):** `english <50:0`, `tamil >6000:0`, `repeat >=8:0`; only **10 fails = missing `550-559`** (catalog gap `idx550→seq560`). No reprocess needed. Existing `501-600:90` + new `601-1024:424` = `1014` = `1024-10`. No zero-english after 2-call fix.
- **Gap pending:** `seq 550-559` never existed on parasakthi WordPress (confirmed `catalog.json:550 idx550 seq560`). Decision deferred per your note — discuss construction/integration later before single-pass fix. No rename mid-batch.

## 1. Goal Accomplished — Prior (2026-09-08 · Periya Puranam Parasakthi 001-500 + Fixes)

- **Parasakthi Periya Puranam pipeline** — `https://parasakthifamily.org/periya-puranam/` evaluated: Google Drive only, `1024 entries (1016 unique, 8 dups)` via `D:\nalvar\periapuranam\parasakthi\build_catalog.py:1` -> `catalog.json:508KB` / `catalog.csv:355KB` + `catalog_preview.md`. All entries `Periya Puranam - 001 - Introduction - Play` with `view_url`/`download_url` (`drive.usercontent.google.com/download?id=` verified `audio/mpeg` 13MB).
- **Gemini 2.5 Flash bilingual** — `openrouter/google/gemini-2.5-flash` via `batch_transcribe.py:1` (URL-text knowledge method, no audio download, `$0.0008/file`). Tested `001` + `002` bilingual `periyapuranam-002-tamil.txt:1505` / `english.txt:564` verified, then batched `001-500` (590 tamil + 590 english + 589 meta, 2.2M folder). Patched from single-call `3000 temp0.3` (36 zero English, repeat loops `x363`) to **2-call** `800+800 temp0.7/0.4 top_p0.9 wait1.8s` + repetition detector + retry. Reprocessed 40 fails `reprocess_failed.py:1` `40/40 ok` (`001:9747/0 -> 2754/994`, `192:9737/0 -> 2632/989`).
- **Batch progress (prior)** — `001-050:45ok` (368s), `051-100:50ok` (464s), `101-200:100ok` (862s), `201-300:100ok` (887s), `301-400:100ok` (910s), `401-500:100ok` (1086s with resume), `501-600:90ok` (gap seq 550-559). Total `001-500` + `501-590` (590 seqs done). Logs `batch_*.log` + `reprocess_failed.log:1746`.
- **Catalog gap issue** — `seq 550-559` skipped (`idx 550 -> seq 560`, `idx 549 -> seq 549`) causes `batch 501-600:90 not 100`. Decision: keep `seq` filenames for source correspondence, fix gap single-pass after `1024` complete (wiki + memory saved).

## 1. Goal Accomplished — Prior Session (2026-09-07 · Blog Admin + Share + YouTube + QA)

- **Blog reader share + YouTube** — `blog/index.html:157` per-article share row `WA (#25D366)`/`X`/`FB`/`LI`/`Copy`+native `navigator.share` at `shareRow` (articleUrl `https://nalvar.in/blog/#slug`), `extractYoutubeId`/`youtubeEmbedHtml` handle `watch`/`youtu.be`/`embed`/`shorts`/bare 11-char, auto-embed `!youtube`/`:::youtube`/`![youtube](url)`/bare YT line → `div.yt-embed iframe` `56.25%` `rel=0`.
- **Admin `blog/admin.html:1` private CRUD** — `noindex` + `_headers` `X-Robots-Tag`, auth overlay `ADMIN_PASSWORD nalvar2026` `sessionStorage`, layout `300px|1fr|420px` center max `62dvh` body (toolbar sticky, `docBar` title+slug), right tabbed `Metadata|Preview` (title/excerpt/slug/date/readTime/level/category/headings editor + `Auto-extract` + YT helper `ytInput`→`ytInlinePreview` iframe inline + live `mdToHtml` preview + share preview), fullscreen `⛶ Fullscreen` `F`/`Esc` (hides sidebars, `calc(100dvh - 74px)`), mobile drawer `≤1100px` `☰ Metadata`, save via inline `PUT posts/<slug>.md + blog.json` to `admin-dev-server.mjs`, `localStorage` backup, validation `headings must match ###`.
- **Dev server + scripts** — `scripts/admin-dev-server.mjs:1` Node `8014` (PUT only `blog/blog.json`+`posts/[a-z0-9-].md`, mirrors `dist/`), `serve.ps1:1` PowerShell (frees `8014`, handles double-click), `serve.bat:1` delegates to ps1, `_headers:36` `Cache-Control no-cache` for `admin.html`/`blog.json`/`posts/*.md`.
- **Docs + QA** — `blog/blog-admin-instructions.md:1` (edit/create/delete + inline Save → `git add` → `wrangler deploy` flow, never exposed live), `TESTPLAN.md:1` 16 tests T1-T16 with exact steps/file:block + test slugs `test-admin-plan-01`.

## 1. Goal Accomplished — Prior Session (2026-09-07)

### 1A. PWA / Deployment Quirks (fixed)

- **`manifest.webmanifest:1`** — `id "/"`, `start_url "/"`, `scope "/"` (was `/index.html`), absolute `"/icons/…"` + `"/"` shortcuts; `sw.js:1` `CACHE nalvar-v23` (was v19), `SHELL` absolute `"/"` `"/index.html"` `"/manifest.webmanifest"` + `"/data.json"` `"/remedies.json"`; removed `remedy-sources.md` from `SHELL` (atomic `addAll` failure → "manifest corrupted"), offline fallback `caches.match("/index.html") || "/"` + normalize `307 /index.html → /`; `index.html:14` `manifest?v=23` `sw.js?v=23`.
- **Icons** — regenerated from `images/nalvar-badge-480.webp` (480×297) on paper `#fdf8f0`: `icons/icon-192.png:32KB`, `icon-512.png:183KB`, `maskable-512.png:101KB` (20% pad), `apple-touch-icon.png:31KB`, `favicon.ico:2KB`.
- **Share** — `index.html:138` remedy `wa-share` green `#25D366` WhatsApp label → theme `bg #fff` `border #e7c9a6` `text #7c2d12` share icon (3-node SVG) + `Share` + `navigator.share → wa.me/?text=` fallback.
- **Provenance** — removed `index.html:318` ` — see remedy-sources.md for provenance.` line.
- **Home links** — wrapped `images/siva_with_nandi_transparent.webp` (`#home-emblem:153`) and `images/nalvar-transparent.webp` (`#home-chip:164`) in `<a href="/">` with `activateTab(first)` + `scrollTo` + `replaceState`.

### 1B. SEO P0 (crawlable)

- **SSR static render** — `data.json` + `remedies.json` inlined into `index.html:182` `<div id="panels">` so `curl -s http://127.0.0.1:8013/ | grep Thirunavukkarasar` `0 → 3`, `curl | grep /#appar` `0 → 4`.
- **Head** — `title` `Nalvar — The Four Saivite Saints | Tevaram & Tiruvasagam` (<60), `meta description` 150c, `rel=canonical https://nalvar.in/`, `meta robots index,follow`, `og:type/site_name/locale en_IN/ta_IN/url/title/description/image https://nalvar.in/og-image.jpg 1200×630` `twitter:card summary_large_image`, `JSON-LD WebSite + ItemList Person×4`, `sitemap.xml:1` 6 urls → now 46, `robots.txt` `Sitemap:` after Cloudflare managed block, `_headers:1` no-cache for `manifest/sw/index` + immutable `og-image.jpg`, `og-image.jpg:55KB` (`images/og-image-1200x630.jpg:55KB` `webp:34KB` `png:146KB`).

### 1C. Path Routing + Blog Scaffold

- **`index.html:453`** — `location.pathname.replace(/^\/+|\/+$/g,'')` → `activateTab(path)` `pushState "/"+name` (`/` for first), hash fallback, `popstate` handler; `renderTabs:470` adds `Blog` tab `<a href="/blog/">`; `wrangler.toml:5` `not_found_handling = "single-page-application"` serves `200` for `/appar` on Cloudflare (local `python -m http.server` gives `404` for `/appar` — expected SPA fallback only on Workers).
- **`blog/index.html:1`** — separate `blog/` reader `280px | 820px | 260px` (`<900px` drawer), Nalvar brown/gold `Georgia` `4a2c11/d97706` `e7c9a6`, header single line `32px` ling icon + `Nalvar · Blog` + `Saiva Siddhanta Reader` inline; `search + All Levels:132` moved from header to `leftSidebar` above `Curriculum` (`width:100%`), `Blog` label, `footer` cleaned (removed `local preview`).

### 1D. Blog Content — 39 Detailed Articles (1500-2500w)

- **Curriculum** — `blog-titles.md` + `blog-topics.md` `10` categories under `3` levels (Beginner 14, Intermediate 12, Advanced 13); each `1500-2500w`, `3` headings, `<p><h3 id><ul><blockquote>` with **inline** `[text](https://shaivam.org|projectmadurai.org|wisdomlib.org|archive.org)` + `youtube.com/results?search_query=` per article, primary only (no random secondary).
- **Generation** — `generate_pilots.py` etc → `generated_articles.json` `pilot_5_detailed.json` `intermediate_articles.json` `advanced_articles.json` `remaining_advanced_articles.json` → `merge_blog.py` → `blog.json:591KB` pooled (deduped 11 duplicates). Verified word counts e.g. `who-were-the-nayanmars 2319w`, `decoding-unmai-vilakkam 1839w`.
- **Friction pass** — inline links moved to `References` then **reverted** per owner: 431 inline links restored, word `provenance`/`algorithm` removed then re-added via rebuild, left-pane `undefined` fix `blog/index.html:220` `${esc(lv.label)}`.

### 1E. Markdown Split — Option A (Approved 2026-09-07)

- **`blog.json:605917 → 42175 bytes` (92.9% drop)** — light index only `{slug,title,excerpt,date,readTime,level,category,headings}`; `blog.full.json:591KB` backup preserved; `blog/posts/*.md:39× ~13.3KB 518KB total` each `---` YAML frontmatter (`slug/title/excerpt/date/readTime/level/category/headings: id/text`) + markdown body (`###` headings `> blockquote` `- list` `**bold**` `*italic*` `[links](https://…)`).
- **Fix** — `scripts/split-blog.py:50` `href=["']` handled both `"` and `'` (stubbed `beyond-the-surface…` `0 → 14` links); `main()` falls back to `blog.full.json` when `SRC` is light.
- **`blog/index.html:166`** — `BLOG_URL ./blog.json` index → `allArticles` flatten → `renderCurriculum()`; `navigate(slug)` async `fetch ./posts/${slug}.md` → `parseFrontmatter()` → `mdToHtml()` (bold/italic/links/lists/blockquote/`h3 id` from `art.headings`) + `mdCache` Map, TOC from index headings immediate, `Next` card, `history.replaceState #slug` + dynamic `canonical` `og:url/title/description` `twitter:title/description` update.

### 1F. Sitemap + OG + Deploy

- **`sitemap.xml:1`** rebuilt via python from `blog.json` dates to **46 urls** (`/` + 4 saints + remedies + `/blog/` + 39 `/blog/#<slug>` with `<lastmod>2026-08-24…2026-09-08</lastmod>` `monthly 0.6`). Verified `curl /sitemap.xml 200`.
- **`blog/index.html:6`** added `robots`, `og:*`, `twitter:*`, `Blog JSON-LD`, fixed `canonical /blog/`; `navigate()` patches them per article (`https://nalvar.in/blog/#slug`).
- **Deploy** — `git 4ba681c feat(blog): per-article markdown, sitemap+OG…` (44 files: `blog/blog.json`, `blog/index.html`, `blog/posts/*.md`, `index.html`, `sitemap.xml`, `scripts/split-blog.py`) + `2511909 chore: wrangler assets -> ./dist` (`directory "./"` → `"./dist"` to prevent `.git` exposure; previous 132 assets leaked `.git/objects`, now 104 clean). `npx wrangler deploy` → `https://nalvar.srirambm.workers.dev` `Version 83cd591e / 7c11afdc` `200` for `/`, `/blog/`, `/blog/blog.json`, `/blog/posts/who-were-the-nayanmars.md`; `https://nalvar.in` `200 HIT`; `.git/COMMIT_EDITMSG` now SPA fallback HTML (no raw leak).

---

## 2. Architectural Decisions Made

- **Blog is separate `blog/index.html`**, not a 6th tab in `index.html` — 3-col reader vs carousel, brown/gold continuity, `Blog` label, `/blog/` path.
- **Pooled `591KB` → per-file `13KB` lazy** — initial `blog.json` `42KB` for syllabus/search/TOC, article `fetch ./posts/${slug}.md` on demand, `mdCache` for back-nav. Enables `git log --follow posts/<slug>.md`, private CRUD via `POST /posts/*.md` + `blog.json` patch, and future per-article `sitemap` + `og` static generation.
- **Primary sources only** (`shaivam.org`, `projectmadurai.org`, `wisdomlib.org`, `archive.org`, `youtube.com/results`) — user preference; inline links retained (References move rejected).
- **Markdown A > JSON B** for CRUD — `textarea` for `md` vs `contenteditable` HTML; `591KB` → `42KB` index keeps search client-side without parser until article open.
- **Path routing via `wrangler.toml` SPA** — `not_found_handling single-page-application` serves `index.html` for `/appar`; local `python -m http.server` `404` for `/appar` is expected, not a bug.
- **`./dist` as deploy source** — `wrangler.toml:5` now `directory "./dist"` (104 files) to avoid uploading `.git/.ocgraph/*.py` (was 132). `dist/` is built by `cp` from root (see §5).

---

## 3. Immediate Next Steps (Day 6 — Day5 6/6 Done, Next is Day6 96F)

1. **Day 6 transcribe Pass 1 — 96F 336ch:** `Chandesura 18F (TBD), Karaikal Ammaiyaar 18F, Kazharitrarivar 28F, Kannappa 32F` — largest small-batch. Use two-pass: run transcribe only (`run_chandesura...`) 2-parallel, verify `Chapter N==files`, `no ====`, dur-aware anomalies + `ffprobe Invalid` re-download. Expected `~45m wall chunked`.
2. **Day 6 translate Pass 2 — chunked English:** Each `18-32F` Tamil `~250-400K chars` → `english_real` `4-7` chunks per story (`limit 60K`), same meter as `run_day05_translate.py:1`. After Day6 English, small batch `65 stories 408F` complete. Then `Day 7 Sundarar 36F` (exception) + buffer.
3. **Deferred anomalies batch (end of Days 1-7):** Fix `KazharChinga 987 41832` + `Thillai 053 0-char` single-chunk re-transcribe (dur-aware now), flip `Anomalies OPEN→Done`; keep `Poyyadiai 967 WRONG` flagged for final review. Then `Day1-5 Human Verified No→Yes` after spot-listen `±1` audio per story (pilot drift check).
4. **Giants deferred `>=50F`:** `Yeyar Kon 62, Thirunavukkarasu 215, ThiruGnanaSambandha 291 568F $27.1 13.8h seq` `Day 10` buffer + `Day 11+` — chunked translate `2-3` calls each (Sambandha `291F 3.2M chars 1.1M tokens $3.42`). Sundarar `36F` exception Day7 deferred.

## 3. Immediate Next Steps (for next session — PAUSED for review per owner 2026-09-08) [ARCHIVED — Day1 done, see above]

1. **Periya Puranam 601-1024 — DONE** `1014 files` (`tamil/english/bilingual/meta` each) in `periapuranam/parasakthi/` — `601-700:100ok`, `701-800:100ok`, `801-900:100ok+1 dup skip`, `901-1000:100ok`, `1001-1024:24ok`; audit `1-1024` clean except `550-559` missing. **STOP — await owner review before any gap fix or book integration.** Do NOT run gap fix script or rename `seq→idx` until discussed.
2. **Periya Puranam gap + book integration — DEFERRED per owner** — `seq 550-559` gap (catalog `idx550→seq560`) + integration of `periapuranam/parasakthi/*` into book: **discuss construction approach next** (owner noted prior plan "cannot be constructed/integrated in that manner"). Keep `seq` filenames stable.
3. **Admin QA — 39 posts (TESTPLAN.md:1, 16 tests T1-T16)** — run on `http://127.0.0.1:8014` via `serve.ps1`/`serve.bat` (Node `admin-dev-server.mjs:1`). T1 auth, T2 search/level filter, T3 open `who-were-the-nayanmars`, T4 toolbar B/I/H3/quote/list (Ctrl+B/I), T5 link, T6 YouTube, T7 metadata+Auto-extract, T8 validation, T9 create `test-admin-plan-01` Save → `PUT blog.json + posts/*.md 200`, T10 share row, T11 edit, T12 slug rename, T13 delete, T14 fullscreen + drawer, T15 Copy MD, T16 deploy flow.
4. **True per-article SEO + dist build** — generate `dist/blog/<slug>/index.html` SSR, `sitemap.xml` to `/blog/<slug>/`, formalize `scripts/build-dist.mjs` (`cp` to `dist/`), `npx wrangler deploy --dry-run` `~105` files, `curl` hygiene checks.

---

## 4. Watch Outs / Edge Cases

- **Periya Puranam seq gap 550-559** — `catalog.json:550` `idx 550 -> seq 560` (10 titles skipped on WordPress). `seq`-based filenames have hole `550-559` never exist; `batch 501-600` yields `90 not 100`. Keep `seq` for source correspondence now, fix single-pass after `1024` complete before book integration. Do not rename mid-batch.
- **Gemini batch repetition** — single-call `3000 temp0.3` caused loops `x363` + `finish:length` truncation -> `english 0`. Patched to 2-call `800+800 temp0.7/0.4` + detector. If future batches show `english <50` or `tamil >6000`, reprocess via `reprocess_failed.py` pattern. Cost ~`$0.002/seq` (2 calls).
- **`./dist` is now the deploy source** — `wrangler.toml:5` `directory "./dist"`; running `npx wrangler deploy` without rebuilding `dist/` will deploy stale `blog/posts/*.md`/`blog.json`/`sitemap.xml`. Always `cp` to `dist/` before deploy or use `scripts/build-dist.mjs`.
- **Hash `/#slug` sitemap** — Google ignores fragments; current `https://nalvar.in/blog/#who-were-the-nayanmars` is discoverable but not indexable as distinct URL. Next step #2 fixes this with `/blog/<slug>/`. Dynamic `og` update in `blog/index.html:360` helps JS-aware sharers only; crawlers without JS see only `/blog/` `og`.
- **`blog/blog.full.json` is local backup** — `605917` bytes, not in git (untracked). `scripts/split-blog.py` falls back to it when `blog.json` is light; don't delete. Generation intermediates `blog/generated_articles.json`, `intermediate_articles.json`, `advanced_articles.json`, `pilot_5_detailed.json`, `remaining_advanced_articles.json`, `blog.merged.json` are also untracked (keep locally for audit, not for deploy).
- **Root `*.py` generators** (`generate_*.py`, `expand*.py`, `merge_blog.py`, `revert_to_3headings.py`) are untracked helpers — do not commit without review; they contain single-quote href fix history.
- **Single-quote `href='…'`** — `scripts/split-blog.py:50` now handles `"`, `'`, and `"` via `["']`; if adding future articles with `href` without quotes, regex will miss — enforce `"` in generator.
- **Local `python -m http.server` vs Workers** — `/appar` `404` locally is expected (no SPA fallback); test path routing on `https://nalvar.srirambm.workers.dev/appar` (`200`) not local.
- **`PILLOW` image pipeline** — `images/optimized/*-800.webp` `26-36KB` via `D:\nalvar\scripts\split-blog.py` era; `icons/*` from `nalvar-badge-480.webp` on `#fdf8f0`; don't reintroduce green WhatsApp label — theme is `#fff`/`#e7c9a6`/`#7c2d12`.

---

## 5. File Manifest (relevant files)

- **Core PWA:** `D:\nalvar\index.html:1` (4 saints + remedies, SSR panels, path routing `453`, `Blog` tab `472`), `D:\nalvar\manifest.webmanifest:1` (`id / start_url / scope`), `D:\nalvar\sw.js:1` (`CACHE v23`), `D:\nalvar\data.json:1` (4 saints), `D:\nalvar\remedies.json:1` (8 cats), `D:\nalvar\sitemap.xml:1` (46 urls), `D:\nalvar\robots.txt:1`, `D:\nalvar\_headers:1`, `D:\nalvar\wrangler.toml:5` (`assets ./dist` `not_found_handling single-page-application`), `D:\nalvar\og-image.jpg` + `D:\nalvar\images\og-image-1200x630.*`, `D:\nalvar\icons/*`, `D:\nalvar\images/optimized/*-800.webp`.
- **Blog:** `D:\nalvar\blog\index.html:1` (3-col, `leftSidebar:132` search, `166` lazy md, `360` `pilot preview` removed, `6` OG), `D:\nalvar\blog\blog.json:1` (`42KB` light index), `D:\nalvar\blog\blog.full.json` (backup `591KB` untracked), `D:\nalvar\blog\posts/<slug>.md:1` (`39×` `---` frontmatter + body, `who-were-the-nayanmars.md:82` lines etc.), `D:\nalvar\scripts\split-blog.py:1` (html→md, `href=["']`).
- **Deploy mirror:** `D:\nalvar\dist/` (`index.html`, `manifest.webmanifest`, `sw.js`, `data.json`, `remedies.json`, `sitemap.xml`, `robots.txt`, `_headers`, `og-image.jpg`, `icons/*`, `images/*`, `blog/index.html`, `blog/blog.json`, `blog/posts/*.md`) — **104 files** `3.3M`.
- **Untracked intermediates:** `D:\nalvar\blog/generated_articles.json`, `advanced_articles.json`, `intermediate_articles.json`, `pilot_5_detailed.json`, `remaining_advanced_articles.json`, `blog.merged.json`, `D:\nalvar\expand*.py`, `generate_*.py`, `merge_blog.py`, `revert_to_3headings.py`, `.ocgraph/`.

---

## 6. Verification (last session)

```bash
python3 -m http.server 8019 --directory D:\nalvar
curl -s http://127.0.0.1:8019/blog/blog.json | wc -c          # 42175
curl -s http://127.0.0.1:8019/blog/posts/who-were-the-nayanmars.md | head -n 20  # frontmatter + markdown
# live
curl -s https://nalvar.srirambm.workers.dev/blog/blog.json | head -c 300  # 42KB light
curl -s https://nalvar.srirambm.workers.dev/sitemap.xml | grep -c "<loc>" # 46
curl -s https://nalvar.srirambm.workers.dev/.git/COMMIT_EDITMSG | head -c 15  # <!DOCTYPE html> (SPA fallback, not raw)
curl -s https://nalvar.in/blog/ -I | grep HTTP  # 200
```

---

## 7. Git State

- `D:\nalvar` `main` at `2511909` (after `4ba681c feat(blog): per-article markdown…`), `origin/main` up to date, `git status` clean except `dist/` + `blog/*.json` intermediates + root `*.py` + `.ocgraph/` untracked (intentional).
- `D:\knowledge-base` `main` at `1a8fd70 docs: handoff 2026-09-07 — Nalvar Blog Phase 2…`, pushed.

---

## 8. Session Token Count

**Session 2026-09-15 Day5 3/6 3-parallel + fix + wrapper:** REAL billed **1,928,656** (RAW 10,036,348, **80.8% caching**, **90.2% hit**, **84 req**) — budget fail-fast patch 60 runners + 3-parallel 120ch 38m wall (Murthi/Tiru/Appoothi 43/35/42ch) + 524 30s re-transcribe 397c + re-translate 99k + run_day05_batch wrapper + tracker fix.

**Session 2026-09-10 Day3 (5/11 + truncation fix):** REAL billed **1,418,301** (RAW 9,371,266, **84.9% caching**, **94.7% hit**, **84 req**) — 11 runners + 5× transcribe/translate + 4× retranslate 30000 + audit.

**Session 2026-09-10 Day2 (14/14):** REAL billed **2,989,614** (RAW 19,798,705, **84.9% caching**, **94.7% hit**, **160 req**) — Day2 14 stories sequential + Anomalies tab + selective backup.

**Session 2026-09-08 cont. (periapuranam 601-1024):** REAL billed **972,432** (RAW 3,797,491, **74.4%** caching, **83.1%** hit, **42** req) — batches 601-1024 (424 seqs, 2-call) + audit + 002 meta fix.

**Session 2026-09-08 (periapuranam 001-500):** REAL billed **1,733,411** (RAW 9,247,621, **81.3%** caching, **90.6%** hit, **98** req) — catalog 1024 + Gemini 001-500 bilingual batches + 40 reprocess fix + seq gap triage.

**Session 2026-09-07 (admin):** cache metrics 92.0% hit, 13,995 req aggregate; prior 4,008,045 REAL billed (86.5% caching, 96.5% hit, 259 req) — PWA/SEO/Blog.

---

## 9. Periyapuranam Nayanar Story Build — New Track (2026-09-09 · Anaya Pilot + Strategy)

- **Source revalidated:** `periapuranam/nvl_catalog.xlsx:catalog 1024 rows (81 unique nayannaar name) / Nayanmar Names 71 rows (63 Thani + 9 Thogai)` → matched `976 rows / 968 unique file_id` (8 dup flags). Unmatched 13 names (`Intro, Sekkizhar... Vellanai Charukkam, Manu Needhi Cholan` etc.) kept out of 71-target build. `Sundarar 36 files` deferred.
- **Anaya pilot `seq 173-179` (`D:\nalvar\periapuranam\_test_merge\anaya_nayanar/`):** Downloaded 6 unique mp3 `12.1–18.7 MB` / `747–1157s` avg `3s/file` → chunked `300s` via `ffmpeg -b:a 64k` (`2.3MB/chunk`) → transcribed real audio via `google/gemini-2.5-flash` (OpenRouter `image_url` `data:audio/mpeg;base64`, `temperature 0.1`) — `prompt 7511 (audio 7500) / completion 892` cost `$0.0096/chunk` (pricing `prompt $0.30/1M audio $1.00/1M completion $2.50/1M`). 21 chunks `$0.20`. `175` kept independently per request (same `fid` as `174` but verified `0.9824` ratio, not assumed duplicate) then removed to `Chapter 01..06` for final story `anaya_nayanar_tamil.txt` `64845 chars / 177KB` (no `====`/`PART`). English single-call `prompt 17857/completion 16182` `$0.045` → `anaya_nayanar_english.txt` `66881 chars / 67KB`. Size diff is UTF-8 `Tamil 3B/char` vs English `1B/char` (`2.74 vs 1.00`).
- **Strategy saved:** `docs/download_strategy.md:1` (catalog truth, measured pipeline, estimates table, day-wise plan 3h/day). `docs/day_wise_plan.xlsx` + `periapuranam/day_wise_plan.xlsx` (`DayWise_Plan` sheet + `Instructions`) now includes Column D **Nayanar Names (Plan)** per day for human tracking: Day1 `21×1-file` (Moorkka…Vayilar), Day2 `8×2+6×3=34 files`, Day3 `3×4+4×5+4×6=56`, Day4 `2×7+3×8+2×9=56` (Anaya ref), Day5 `2×11+1×12+3×13=73`, Day6 `2×18+28+32=96`, Day7 `2×36=72` (Sundarar deferred), Day8 English `65 stories`, Day9 QA, Day10 buffer. Totals `Small <50 408 files 1428 chunks $17.2 9.9h seq / 2.5h 4-worker`; giants `>=50 568 files $27.1 13.8h seq`. Overall `976 files $44-45 23.8h seq / 5.9h 4-worker` → **~10 days @3h/day**.
- **Actuals workflow:** At every session end, fill `day_wise_plan.xlsx` Actuals columns `J Actual Date / K Files Done / L Time / M Cost (sum usage.cost) / N Notes / O Status dropdown (Not Started/In Progress/Done/Blocked)`. Parse `tamil_real/transcribe_log.json` + `anaya_english_meta.json` for cost. Reversible via `_test_merge` folder; promotion to `periapuranam/output/` only after Day9 QA.
- **Memory:** `mem_1788937672685_khfgr` (pilot), `mem_1788937683149_xx2dn` (plan/convention), `mem_1788937694608_norxf` (close-work ritual) saved in project scope.

*Next session: resume from `docs/day_wise_plan.xlsx` Day 1 — 21×1-file batch (Moorkka…Vayilar). Run Day 1 transcribe, fill Actuals J-M, then close-work per ritual. Do NOT start giants (Yeyar 62 / Thirunavukkarasu 215 / Sambandha 291) until Day9 QA sign-off.*

---

*Previous next: discuss periapuranam gap 550-559 + book-integration (PAUSED), then blog admin QA `TESTPLAN.md` T1-T16 on `http://127.0.0.1:8014/blog/admin.html`.*

(End of file - total 147 lines)
