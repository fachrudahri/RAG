# utils/loaders.py
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

SUPPORT_TXT = {".txt", ".md", ".json", ".csv"}

def load_corpus(root: str) -> List[Document]:
    docs: List[Document] = []
    base = Path(root)
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in SUPPORT_TXT:
            loader = TextLoader(str(p), encoding="utf-8")
            loaded = loader.load()
        elif ext == ".pdf":
            loader = PyPDFLoader(str(p))
            loaded = loader.load()
        else:
            # other formats: convert first to .md/.txt
            continue

        parts = p.relative_to(base).parts  # ex: nextjs/15/en/file.md
        meta = {
            "source_path": str(p),
            "framework": parts[0] if len(parts) > 0 else "",
            "version":  parts[1] if len(parts) > 1 else "",
            "lang":     parts[2] if len(parts) > 2 else "",
            "filename": p.name,
        }
        for d in loaded:
            d.metadata.update(meta)
        docs.extend(loaded)
    return docs
