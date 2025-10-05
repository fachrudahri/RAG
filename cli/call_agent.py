#!/usr/bin/env python3
# cli/call_agent.py — call-agent with profiles, scoring, and auto-fallback
import os
import sys
import time
import argparse
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from qdrant_client.http import models as qm

# ---------- Project root & config files ----------
PROJECT_ROOT = os.path.expanduser(os.getenv("RAG_HOME", "~/RAG"))
os.chdir(PROJECT_ROOT)

PROFILES_PATH = os.path.join(PROJECT_ROOT, "profiles.yaml")
CURRENT_PROFILE_PATH = os.path.join(PROJECT_ROOT, ".profile_current")

# ---------- Environment ----------
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "kb_global")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful, bilingual (English & Indonesian) assistant.

TARGET LANGUAGE: {lang_label}

Rules:
- Answer **only** in the target language above.
- Length: aim for **4–8 sentences** (or concise bullet points) — not too short, but clear.
- Use code blocks when helpful.
- Rely **strictly** on the provided context. If the answer is not present in the context, reply exactly:
  • English → "Not found in the documents."
  • Indonesian → "Tidak ditemukan di dokumen."

# Question
{question}

# Context
{context}
"""
)

console = Console()

# ---------- Profile helpers ----------
def load_profiles():
    if not os.path.isfile(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("profiles", {}) or {}

def read_current_profile():
    if os.path.isfile(CURRENT_PROFILE_PATH):
        with open(CURRENT_PROFILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def write_current_profile(name: str):
    with open(CURRENT_PROFILE_PATH, "w", encoding="utf-8") as f:
        f.write(name or "")

def build_filter_from_profile_dict(pdef: dict | None):
    if not pdef:
        return None
    must = []
    for k in ("framework", "version", "lang"):
        v = pdef.get(k)
        if v:
            must.append(qm.FieldCondition(key=k, match=qm.MatchValue(value=str(v))))
    return qm.Filter(must=must) if must else None

# ---------- Heuristic profile guess ----------
def guess_profile_from_query(q: str) -> str | None:
    ql = q.lower()
    # Next.js / React heuristics
    if any(w in ql for w in [
        "nextjs", "next.js", "next js", "react server component", "rsc",
        "app router", "route handler", "server action", "middleware", "layout.tsx"
    ]):
        return "nextjs15-en"
    # NestJS heuristics
    if any(w in ql for w in [
        "nestjs", "nest.js", "nest js", "controller", "provider", "module",
        "decorator", "guard", "interceptor", "pipe"
    ]):
        return "nestjs11-en"
    return None

def detect_lang(q: str) -> str:
    """Very simple heuristic: return 'en' or 'id'."""
    s = (q or "").lower()
    # kata-kata penanda
    en_markers = {"how", "what", "why", "when", "where", "please", "example", "explain", "create", "generate"}
    id_markers = {"bagaimana", "apa", "mengapa", "kapan", "dimana", "contoh", "tolong", "buatkan", "jelaskan"}
    en_hits = sum(1 for w in en_markers if w in s)
    id_hits = sum(1 for w in id_markers if w in s)
    # fallback: karakter
    if en_hits > id_hits:
        return "en"
    if id_hits > en_hits:
        return "id"
    # fallback lagi: jika huruf & spasi latin tanpa aksen, anggap en
    try:
        s.encode("ascii")
        return "en"
    except Exception:
        return "id"


# ---------- Core ----------
def retrieve_and_answer(question: str, profile_name: str | None, k: int = 8):
    profiles = load_profiles()
    profile_def = profiles.get(profile_name) if profile_name else None
    qfilter = build_filter_from_profile_dict(profile_def)

    t0 = time.time()
    embeddings = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)
    vs = QdrantVectorStore.from_existing_collection(
        url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )

    # helper: run retrieval with scores and simple relevance gate
    def retrieve_with_scores(q, flt):
        hits = vs.similarity_search_with_score(q, k=k, filter=flt)
        # Qdrant cosine distance: smaller = better
        threshold = 0.8
        kept = [(d, s) for (d, s) in hits if s <= threshold]
        return kept or hits

    # 1) Try with active filter (if any)
    hits = retrieve_with_scores(question, qfilter)
    used_profile = profile_name

    # 2) If no filter (ALL) and results look weak, try heuristic profile fallback
    if not qfilter:
        weak = (len(hits) == 0) or (hits[0][1] > 0.9)
        if weak:
            guessed = guess_profile_from_query(question)
            if guessed and guessed in profiles:
                gf = build_filter_from_profile_dict(profiles[guessed])
                hits2 = retrieve_with_scores(question, gf)
                if hits2:
                    hits = hits2
                    used_profile = guessed  # indicate fallback in UI

    t1 = time.time()
    docs = [h[0] for h in hits]

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
    lang = detect_lang(question)
    lang_label = "English" if lang == "en" else "Indonesian"
    chain = PROMPT | llm
    answer = chain.invoke({"question": question, "context": context, "lang_label": lang_label})
    t2 = time.time()

    timings = (t1 - t0, t2 - t1)
    prof_def_final = profiles.get(used_profile) if used_profile else None
    return answer.content, docs, timings, (used_profile or "all"), prof_def_final

def print_answer(answer: str, docs, timings, profile_name, profile_def):
    # Header profile
    prof_meta = ", ".join([f"{k}={v}" for k, v in (profile_def or {}).items()]) or "no filter"
    console.print(Panel.fit(f"[bold]profile:[/bold] {profile_name}  [dim]({prof_meta})[/dim]", border_style="green"))

    # Result block
    console.print(Panel.fit("[bold]result:[/bold]", border_style="cyan"))
    console.print(Markdown(answer))

    # Sources table
    table = Table(title="sources", title_style="bold", show_header=True, header_style="bold magenta")
    table.add_column("#", width=3)
    table.add_column("path", overflow="fold")
    table.add_column("meta", overflow="fold")
    for i, d in enumerate(docs, start=1):
        meta = f"{d.metadata.get('framework','')}/{d.metadata.get('version','')}/{d.metadata.get('lang','')}"
        table.add_row(str(i), d.metadata.get("source_path", "-"), meta)
    console.print(table)

    # Timings
    r, g = timings
    console.print(f"[dim]retrieval {r:.3f}s | generation {g:.3f}s[/dim]")

def handle_repl_cmd(cmd: str, session_profile: str | None):
    """
    REPL commands: :profile list | :profile show | :profile set <name>|all
    Returns possibly-updated session_profile (None means 'all').
    """
    parts = cmd.strip().split()
    if not parts or parts[0] != ":profile":
        return session_profile  # no-op

    profiles = load_profiles()
    sub = parts[1] if len(parts) > 1 else ""

    if sub == "list":
        console.print("[bold]Profiles available:[/bold]")
        for name, pdef in profiles.items():
            meta_items = []
            if pdef:
                for k, v in pdef.items():
                    meta_items.append(f"{k}={v}")
            meta = ", ".join(meta_items) if meta_items else "no filter"
            console.print(f"- {name}  [dim]({meta})[/dim]")
        # tampilkan 'all' hanya jika tidak didefinisikan di profiles.yaml
        if "all" not in profiles:
            console.print("- all  [dim](no filter)[/dim]")
        return session_profile

    elif sub == "show":
        cur = session_profile or "all"
        console.print(f"[bold]Current (session):[/bold] {cur}")
        persisted = read_current_profile() or "all"
        if (session_profile or "all") != persisted:
            console.print(f"[dim]Default (saved): {persisted}[/dim]")
        return session_profile

    elif sub == "set":
        if len(parts) < 3:
            console.print("[red]Usage:[/red] :profile set <name>|all")
            return session_profile
        name = parts[2]
        if name != "all" and name not in profiles:
            console.print(f"[red]Unknown profile:[/red] {name}")
            return session_profile
        # update default (file) + session
        write_current_profile("" if name == "all" else name)
        console.print(f"[green]Profile set to:[/green] {name}")
        return None if name == "all" else name

    else:
        console.print("[red]Unknown subcommand.[/red] Use :profile list | :profile show | :profile set <name>|all")
        return session_profile

def main():
    ap = argparse.ArgumentParser(description="call-agent with profiles, scoring, and auto-fallback")
    ap.add_argument("-p", "--profile", help="Profile name (overrides current). Use 'all' for no filter.")
    ap.add_argument("--set-profile", help="Set default profile and exit. Use 'all' to clear.")
    ap.add_argument("-k", "--topk", type=int, default=8, help="Top-k retrieval (default 8)")
    ap.add_argument("question", nargs="*", help="Question (if empty → REPL mode)")
    args = ap.parse_args()

    # Set default profile and exit
    if args.set_profile is not None:
        name = args.set_profile
        if name == "all":
            write_current_profile("")
            console.print("[green]Default profile cleared (all).[/green]")
            return
        profiles = load_profiles()
        if name not in profiles:
            console.print(f"[red]Unknown profile:[/red] {name}")
            return
        write_current_profile(name)
        console.print(f"[green]Default profile set to:[/green] {name}")
        return

    # Resolve active profile
    if args.profile:
        active_profile = None if args.profile == "all" else args.profile
    else:
        cur = read_current_profile()
        active_profile = cur if cur else None

    # One-shot
    if args.question:
        question = " ".join(args.question)
        answer, docs, timings, pname, pdef = retrieve_and_answer(question, active_profile, k=args.topk)
        print_answer(answer, docs, timings, pname, pdef)
        return

    # REPL
    session_profile = active_profile  # start from resolved active
    prof_label = session_profile or "all"
    console.print(f"[bold]call-agent[/bold] — REPL mode. Current profile: [green]{prof_label}[/green]")
    console.print("[dim]Commands: :profile list | :profile show | :profile set <name>|all[/dim]")
    while True:
        try:
            q = console.input(">>> ").strip()
            if not q:
                continue
            if q.startswith(":"):
                session_profile = handle_repl_cmd(q, session_profile)
                continue
            # retrieve_and_answer() sekarang return 5 values:
            # (answer, docs, timings, profile_used, profile_def)
            answer, docs, timings, pname, pdef = retrieve_and_answer(
                q, session_profile, k=args.topk
            )
            # print_answer() terima 5 argumen juga
            print_answer(answer, docs, timings, pname, pdef)
        except KeyboardInterrupt:
            console.print("\n[dim]bye[/dim]")
            break




if __name__ == "__main__":
    main()
