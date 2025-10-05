#!/usr/bin/env python3
import os, re, sys, shutil, pathlib

SRC = os.path.expanduser("~/tmp/docs.nestjs.com/content")
DST = os.path.expanduser("~/RAG/corpus/nestjs/11/en")

FRONTMATTER_TMPL = (
    "---\n"
    "framework: nestjs\n"
    'version: "11"\n'
    "lang: en\n"
    "site: docs.nestjs.com\n"
    "source: \"local://nestjs-repo/{rel}\"\n"
    "---\n\n"
)

# MDX cleanup heuristics
RE_IMPORT = re.compile(r"^\s*import\s+.+?from\s+['\"].+?['\"]\s*;?\s*$")
RE_EXPORT = re.compile(r"^\s*export\s+(const|default)\s+.+$")
RE_TS_BLOCK = re.compile(r"^<\s*Tabs?[\s>].*|^</\s*Tabs?\s*>$")
RE_CALLOUT_OPEN = re.compile(r"^<\s*Callout[^>]*>$")
RE_CALLOUT_CLOSE = re.compile(r"^</\s*Callout\s*>$")
RE_COMPONENT_TAG = re.compile(r"^<\s*[A-Z][A-Za-z0-9]*(\s[^>]*)?>\s*$")
RE_COMPONENT_CLOSE = re.compile(r"^</\s*[A-Z][A-Za-z0-9]*\s*>\s*$")
RE_EMPTY_HTML = re.compile(r"^\s*<br\s*/?>\s*$")

def convert_mdx_text(text: str) -> str:
    out = []
    skip_block = False
    for line in text.splitlines():
        if RE_IMPORT.match(line) or RE_EXPORT.match(line):
            continue
        if RE_TS_BLOCK.match(line):
            continue
        if RE_CALLOUT_OPEN.match(line):
            out.append("> **Note**")
            skip_block = False
            continue
        if RE_CALLOUT_CLOSE.match(line):
            skip_block = False
            continue
        if RE_COMPONENT_TAG.match(line) or RE_COMPONENT_CLOSE.match(line) or RE_EMPTY_HTML.match(line):
            continue
        out.append(line)
    # tidy up extra blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"
    return cleaned

def process_file(src_path: str, dst_root: str):
    rel = os.path.relpath(src_path, SRC)
    # normalize extension to .md
    rel_md = os.path.splitext(rel)[0] + ".md"
    dst_path = os.path.join(dst_root, rel_md)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    with open(src_path, "r", encoding="utf-8") as f:
        text = f.read()

    if src_path.endswith(".mdx"):
        body = convert_mdx_text(text)
    else:
        body = text

    fm = FRONTMATTER_TMPL.format(rel=rel.replace("\\", "/"))
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    return dst_path

def main():
    if not os.path.isdir(SRC):
        print(f"Source not found: {SRC}")
        sys.exit(1)
    os.makedirs(DST, exist_ok=True)
    count = 0
    for root, _, files in os.walk(SRC):
        for name in files:
            if not (name.endswith(".md") or name.endswith(".mdx")):
                continue
            src = os.path.join(root, name)
            out = process_file(src, DST)
            count += 1
            if count % 20 == 0:
                print(f"[{count}] {out}")
    print(f"Done. Converted {count} files into {DST}")

if __name__ == "__main__":
    main()
