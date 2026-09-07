#!/usr/bin/env python3
"""Split D:\nalvar\blog\blog.json -> D:\nalvar\blog\posts\<slug>.md (frontmatter + markdown) + light index."""
import json, re, pathlib, html

SRC = pathlib.Path("D:/nalvar/blog/blog.json")
OUT_DIR = pathlib.Path("D:/nalvar/blog/posts")
BACKUP = pathlib.Path("D:/nalvar/blog/blog.full.json")

def html_to_md(html_str: str) -> str:
    s = html_str
    # normalize whitespace
    s = s.replace("\r\n","\n")
    # preserve headings first
    # <h3 id="x">text</h3> -> ### text
    def repl_h3(m):
        txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        txt = html.unescape(txt)
        # we keep id as anchor via heading text; optionally add {#id}
        hid = m.group(1)
        return f"\n### {txt}\n"
    s = re.sub(r'<h3[^>]*id="([^"]+)"[^>]*>(.*?)</h3>', repl_h3, s, flags=re.DOTALL|re.IGNORECASE)
    s = re.sub(r'<h3[^>]*>(.*?)</h3>', lambda m: f"\n### {html.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())}\n", s, flags=re.DOTALL|re.IGNORECASE)
    s = re.sub(r'<h2[^>]*>(.*?)</h2>', lambda m: f"\n## {html.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())}\n", s, flags=re.DOTALL|re.IGNORECASE)
    # blockquote
    def repl_bq(m):
        inner = m.group(1)
        # strip inner p etc later, but handle
        inner = re.sub(r'<p[^>]*>', '', inner)
        inner = re.sub(r'</p>', '\n', inner)
        inner = re.sub(r'<[^>]+>', '', inner)
        inner = html.unescape(inner).strip()
        lines = inner.splitlines()
        return "\n" + "\n".join("> " + l.strip() for l in lines if l.strip()) + "\n\n"
    s = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', repl_bq, s, flags=re.DOTALL|re.IGNORECASE)
    # lists
    s = re.sub(r'<ul[^>]*>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'</ul>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'<ol[^>]*>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'</ol>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'<li[^>]*>', '- ', s, flags=re.IGNORECASE)
    s = re.sub(r'</li>', '\n', s, flags=re.IGNORECASE)
    # links <a href="url">text</a> -> [text](url)
    def repl_a(m):
        href = m.group(1)
        text = re.sub(r'<[^>]+>', '', m.group(2))
        text = html.unescape(text).strip()
        # escape brackets in text
        text = text.replace('[','\\[').replace(']','\\]')
        return f'[{text}]({href})'
    s = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', repl_a, s, flags=re.DOTALL|re.IGNORECASE)
    # bold/strong
    s = re.sub(r'<strong[^>]*>(.*?)</strong>', lambda m: f"**{html.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())}**", s, flags=re.DOTALL|re.IGNORECASE)
    s = re.sub(r'<b[^>]*>(.*?)</b>', lambda m: f"**{html.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())}**", s, flags=re.DOTALL|re.IGNORECASE)
    # em/i
    s = re.sub(r'<em[^>]*>(.*?)</em>', lambda m: f"*{html.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())}*", s, flags=re.DOTALL|re.IGNORECASE)
    s = re.sub(r'<i[^>]*>(.*?)</i>', lambda m: f"*{html.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())}*", s, flags=re.DOTALL|re.IGNORECASE)
    # paragraphs
    s = re.sub(r'<p[^>]*>', '', s)
    s = re.sub(r'</p>', '\n\n', s)
    # br
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.IGNORECASE)
    # strip any remaining tags
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    # normalize entities for dashes/quotes (html.unescape already)
    # collapse multiple blank lines to max 2
    s = re.sub(r'\n{3,}', '\n\n', s)
    # trim lines trailing spaces
    s = "\n".join(line.rstrip() for line in s.splitlines())
    s = s.strip() + "\n"
    return s

def yaml_escape(v: str) -> str:
    # escape for double-quoted YAML
    return v.replace("\\","\\\\").replace('"','\\"')

def build_frontmatter(art):
    lines = ["---"]
    lines.append(f'slug: {art["slug"]}')
    lines.append(f'title: "{yaml_escape(art["title"])}"')
    lines.append(f'excerpt: "{yaml_escape(art["excerpt"])}"')
    lines.append(f'date: {art["date"]}')
    lines.append(f'readTime: {art["readTime"]}')
    lines.append(f'level: {art["level"]}')
    lines.append(f'category: {art["category"]}')
    if art.get("headings"):
        lines.append("headings:")
        for h in art["headings"]:
            lines.append(f'  - id: {h["id"]}')
            lines.append(f'    text: "{yaml_escape(h["text"])}"')
    lines.append("---")
    return "\n".join(lines)

def main():
    raw = SRC.read_text(encoding="utf-8")
    j = json.loads(raw)
    # if SRC is already light index (no contentHtml), fall back to backup
    has_html = False
    try:
        has_html = any('contentHtml' in a for lv in j['levels'] for cat in lv['categories'] for a in cat['articles'])
    except: pass
    if not has_html and BACKUP.exists():
        print(f"SRC is light index, reading full from {BACKUP}")
        j = json.loads(BACKUP.read_text(encoding="utf-8"))
    # backup full if not exists or SRC was full
    if not BACKUP.exists() and has_html:
        BACKUP.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"backup -> {BACKUP}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for lv in j["levels"]:
        for cat in lv["categories"]:
            for art in cat["articles"]:
                md_body = html_to_md(art["contentHtml"])
                fm = build_frontmatter(art)
                out = OUT_DIR / f"{art['slug']}.md"
                out.write_text(fm + "\n\n" + md_body, encoding="utf-8")
                count += 1
                print(f"wrote {out.name} {len(md_body)} chars")
    # now build light index (strip contentHtml)
    light = {"site": j["site"], "levels": []}
    for lv in j["levels"]:
        nlv = {"id": lv["id"], "label": lv["label"], "tamil": lv.get("tamil",""), "categories": []}
        for cat in lv["categories"]:
            ncat = {"id": cat["id"], "label": cat["label"], "articles": []}
            for art in cat["articles"]:
                ncat["articles"].append({
                    "slug": art["slug"],
                    "title": art["title"],
                    "excerpt": art["excerpt"],
                    "date": art["date"],
                    "readTime": art["readTime"],
                    "level": art["level"],
                    "category": art["category"],
                    "headings": art.get("headings", [])
                })
            nlv["categories"].append(ncat)
        light["levels"].append(nlv)
    SRC.write_text(json.dumps(light, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"light index -> {SRC} size {SRC.stat().st_size/1024:.1f} KB")
    print(f"posts -> {count} files in {OUT_DIR}")
    # list
    import os
    total = sum(p.stat().st_size for p in OUT_DIR.glob("*.md"))
    print(f"total md size {total/1024:.1f} KB avg {total/count/1024:.1f} KB")

if __name__ == "__main__":
    main()
