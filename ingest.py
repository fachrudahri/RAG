# ingest.py — parametris: pilih koleksi & folder korpus
import os
import argparse
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from utils.loaders import load_corpus  # ini sudah ada di proyekmu

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

def main():
    ap = argparse.ArgumentParser(description="Ingest Markdown corpus to Qdrant collection.")
    ap.add_argument("--corpus", default="corpus", help="Folder korpus (default: corpus)")
    ap.add_argument("--collection", required=True, help="Nama koleksi Qdrant (wajib)")
    ap.add_argument("--recreate", action="store_true", help="Drop & create ulang koleksi terlebih dahulu")
    ap.add_argument("--chunk-size", type=int, default=900)
    ap.add_argument("--chunk-overlap", type=int, default=150)
    args = ap.parse_args()

    # (opsional) recreate collection
    if args.recreate:
        try:
            qc = QdrantClient(url=QDRANT_URL)
            qc.delete_collection(args.collection)
            print(f"[info] Dropped collection '{args.collection}'")
        except Exception as e:
            print(f"[warn] delete_collection: {e} (lanjut)")

    raw_docs = load_corpus(args.corpus)
    if not raw_docs:
        print(f"[err] No documents found in {args.corpus}")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        separators=["\n##", "\n#", "\n\n", "\n", " "],
    )
    docs = splitter.split_documents(raw_docs)

    embeddings = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)

    QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,                 # <- singular
        url=QDRANT_URL,
        collection_name=args.collection,
    )
    print(f"[ok] Indexed {len(docs)} chunks into '{args.collection}' from '{args.corpus}'")

if __name__ == "__main__":
    main()
