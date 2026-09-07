# HANDOFF — Nalvar (D:\nalvar)

> **Purpose:** project-local detailed handoff for continued work on `nalvar.in` — PWA, SEO, path routing, and Blog phase 2. The wiki `D:\knowledge-base\HANDOFF.md` is the thin master pointer; this file is the **authoritative project detail**.
>
> **Last updated:** 2026-09-07 · `main` at `2511909` (after `4ba681c`) · deployed `https://nalvar.in` + `https://nalvar.srirambm.workers.dev` Version `83cd591e / 7c11afdc`
>
> **Stack:** static PWA (no framework), `index.html` + `data.json` + `remedies.json` + `blog/` (markdown per-article), Cloudflare Workers Assets (`wrangler.toml` `directory ./dist` `not_found_handling single-page-application`), `sw.js` precache, `manifest.webmanifest`

---

## 1. Goal Accomplished — This Session (2026-09-07)

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

## 3. Immediate Next Steps (for next session)

1. **Private CRUD form** — `blog/admin.html` (auth-gated, not linked) with `title/excerpt/date/readTime/level/category` inputs + `headings` editor + `textarea` for `posts/<slug>.md` (YAML frontmatter + body). On save: `PUT /blog/posts/<slug>.md`, patch `blog/blog.json` index, regenerate `sitemap.xml` `<lastmod>` from `date`, rebuild `dist/blog/` + `dist/sitemap.xml`, `git commit` + `wrangler deploy`. Handle slug rename (file move + index update).
2. **True per-article SEO** — generate `dist/blog/<slug>/index.html` static shell (SSR `md → html` at build) with per-article `<title>`, `<meta description excerpt>`, `<link rel=canonical https://nalvar.in/blog/<slug>/>`, `og:url/title/description/image`, `JSON-LD BlogPosting`, then `sitemap.xml` point to `/blog/<slug>/` not `/#slug`. Keep `blog/#slug` as fallback via `history.replaceState` redirect.
3. **Dist build script** — formalize `scripts/build-dist.mjs` (`cp index.html manifest.webmanifest sw.js data.json remedies.json sitemap.xml robots.txt _headers og-image.jpg icons/* images/* blog/index.html blog/blog.json blog/posts/*.md → dist/`), add `npm run build` + `pre-deploy` hook; add `dist/` to `.gitignore` after deciding whether to track built output.
4. **Verify deploy hygiene** — `npx wrangler deploy --dry-run` `104` files, `curl -s https://nalvar.in/.git/COMMIT_EDITMSG` returns SPA fallback HTML (not raw), `curl -s https://nalvar.in/blog/posts/who-were-the-nayanmars.md | head -n 20` `200` with frontmatter.

---

## 4. Watch Outs / Edge Cases

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

**Session 2026-09-07:** REAL billed **4,008,045** (RAW 29,596,012, **86.5%** caching, **96.5%** hit, **259** req) — PWA fixes, SEO, path routing, 39-article generation + markdown split + sitemap/OG + deploy + `.git` leak fix.

---

*Next session: resume from this file (`D:\nalvar\HANDOFF.md`) — rebuild `dist/` then `blog/admin.html` CRUD.*
