# ingest.py (fix)
import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from utils.loaders import load_corpus

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "kb_global")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

def main():
    raw_docs = load_corpus("corpus")
    if not raw_docs:
        print("No documents found in ./corpus")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n##", "\n#", "\n\n", "\n", " "],
    )
    docs = splitter.split_documents(raw_docs)

    # Embeddings via Ollama
    embeddings = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)

    # Build / upsert into Qdrant (via URL; most stable)
    QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,              # required: singular
        url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
    )

    print(f"Indexed {len(docs)} chunks into '{QDRANT_COLLECTION}'")

if __name__ == "__main__":
    main()
