# ask.py (fix final)
import os, sys
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "kb_global")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

PROMPT = ChatPromptTemplate.from_template(
    """Jawab singkat, akurat, dan **hanya** berdasarkan konteks.
Jika tidak ada di konteks, katakan: "Tidak ditemukan di dokumen."
Bahasa jawaban ikuti bahasa pertanyaan.

# Pertanyaan:
{question}

# Konteks:
{context}
"""
)

def main():
    question = " ".join(sys.argv[1:]) or "Apa itu App Router di Next.js?"

    embeddings = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)

    # >>> use url=, not client= <<<
    vs = QdrantVectorStore.from_existing_collection(
        url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )

    docs = vs.similarity_search(question, k=5)
    context = "\n\n".join(
        [
            f"- ({d.metadata.get('framework','')}/"
            f"{d.metadata.get('version','')}/"
            f"{d.metadata.get('lang','')} - "
            f"{d.metadata.get('filename')})\n{d.page_content}"
            for d in docs
        ]
    )

    llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=LLM_MODEL, temperature=0.2)
    answer = (PROMPT | llm).invoke({"question": question, "context": context})

    print("\n=== ANSWER ===\n", answer.content)
    print("\n=== SOURCES ===")
    for d in docs:
        print(d.metadata.get("source_path"))

if __name__ == "__main__":
    main()
