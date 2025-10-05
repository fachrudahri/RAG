import os, time, urllib.parse, re, sys
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE = "https://nextjs.org"
ROOT = f"{BASE}/docs"
OUT_DIR = "corpus/nextjs/15/en"
HEADERS = {"User-Agent": "LocalRAGFetcher/1.2 (+offline use)"}

SLEEP = 0.3
MAX_PAGES = 1000
SKIP_EXT = (".png",".jpg",".jpeg",".svg",".gif",".ico",".webp",".mp4",".mp3",".pdf",".zip")

seen, queue = set(), [ROOT]

def is_docs_url(url: str) -> bool:
    if not url: return False
    if any(url.lower().endswith(ext) for ext in SKIP_EXT): return False
    return url.startswith(ROOT)

def norm_url(href: str, current: str) -> str:
    url = urllib.parse.urljoin(current, href)
    parsed = urllib.parse.urlparse(url)
    url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    if not url.startswith(BASE): return ""
    return url

def rel_path_from_docs(path: str) -> str:
    rel = path[len("/docs/"):] if path.startswith("/docs/") else path.strip("/")
    if not rel: rel = "index"
    rel = re.sub(r"[^a-zA-Z0-9/_\\-]", "-", rel)
    return rel + ".md"

def add_frontmatter(markdown: str, src_url: str) -> str:
    fm = f"""---
framework: nextjs
version: "15"
lang: en
source: "{src_url}"
---
"""
    return fm + "\n" + markdown

def extract_content_html(soup: BeautifulSoup) -> str:
    """
    Ambil **konten utama** saja; buang nav/footer/aside/script/style/next-data.
    """
# remove non-content elements
    for sel in ["nav", "header", "footer", "aside", "[role=navigation]"]:
        for tag in soup.select(sel):
            tag.decompose()
# remove all <script>, <style>, <noscript> (including __NEXT_DATA__)
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

# prefer <main> if available; otherwise try <article>; fallback to body
    main = soup.find("main")
    if main is None:
        main = soup.find("article")
    if main is None:
        main = soup.body or soup

# Next sometimes inserts comment/placeholder nodes: clean up comments
    for c in main(text=lambda t: isinstance(t, type(soup.comment))):
        c.extract()

    return str(main)

def postprocess_markdown(text: str) -> str:
    """
    Clean-up tambahan: hapus baris JS sisa (jaga-jaga).
    """
# remove blocks/lines containing streaming/hydration patterns
    trash_patterns = [
        r"requestAnimationFrame\(function\)\{\$RT=performance\.now\(\)\}\);\$RB=\[\];",
        r"\$RC=function", r"\$RV=function", r"__NEXT_DATA__", r"\$RT=performance\.now",
    ]
    for pat in trash_patterns:
        text = re.sub(pat, "", text)

# also clean lines that are very long with many $ or function(){…}
    lines = []
    for line in text.splitlines():
        if len(line) > 2000 and ("function(" in line or "$" in line):
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"

os.makedirs(OUT_DIR, exist_ok=True)

count = 0
while queue and count < MAX_PAGES:
    url = queue.pop(0)
    if url in seen:
        continue
    seen.add(url)

    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            print(f"[skip {r.status_code}] {url}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        content_html = extract_content_html(soup)

# convert → markdown (do not strip script/style because they are already decomposed)
        markdown = md(
            content_html,
            heading_style="ATX",
# do not strip script/style here; they have already been removed from the DOM
# strip=["style","script"],
            escape_asterisks=False,
            bullets="*",
        )
        markdown = postprocess_markdown(markdown)
        markdown = add_frontmatter(markdown, url)

        path = urllib.parse.urlparse(url).path
        rel_md = rel_path_from_docs(path)
        out_path = os.path.join(OUT_DIR, rel_md)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        count += 1
        print(f"[saved {count}] {url} -> {out_path}")

# enqueue other /docs links
        for a in soup.find_all("a", href=True):
            u = norm_url(a.get("href"), url)
            if is_docs_url(u) and u not in seen:
                queue.append(u)

        time.sleep(SLEEP)

    except Exception as e:
        print(f"[err] {url} -> {e}", file=sys.stderr)

print(f"Done. Saved {count} pages into {OUT_DIR}")
