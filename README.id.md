# RAG — Setup Qdrant, Ollama, dan Cara Menjalankan

Repositori ini berisi pipeline RAG sederhana dengan:

- Qdrant sebagai vector database (via Docker Compose)
- Ollama untuk embeddings dan LLM
- Skrip Python untuk ingest dokumen dan tanya jawab
- Opsi integrasi n8n (opsional) di shared network `ragnet`

---

## Prasyarat

- macOS dengan akses Terminal
- `Docker` dan `Docker Compose`
- `Python` 3.11+ (disarankan 3.12) dan `pip`
- `Ollama`

---

## Konfigurasi Environment

File `.env` di root dipakai oleh skrip Python. Nilai default sudah aman, tapi bisa disesuaikan:

```
# contoh variabel penting
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=kb_global
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text
RAG_HOME=~/RAG
```

Untuk Docker Compose, masing-masing folder `infrastructure/qdrant` dan `infrastructure/n8n` juga punya `.env` sendiri (lihat README di folder tersebut).

---

## Setup Ollama

1. Instal Ollama (macOS):

- Unduh dari `https://ollama.com/download` atau via Homebrew: `brew install ollama`

2. Jalankan server Ollama:

- `ollama serve` (biarkan berjalan), atau gunakan layanan background jika sudah diset otomatis oleh installer.

3. Tarik model yang dipakai:

- `ollama pull llama3.1:8b`
- `ollama pull nomic-embed-text`

4. Cek status cepat:

- API: `curl -fsS http://localhost:11434/api/tags`

---

## Menjalankan Qdrant (Vector DB)

1. Buat shared network (opsional tapi direkomendasikan):

- `docker network create ragnet`

2. Masuk ke folder Compose Qdrant:

- `cd infrastructure/qdrant`

3. Sesuaikan `.env` minimal:

- `QDRANT_VERSION`, `QDRANT_HTTP_PORT`, `QDRANT_GRPC_PORT`, `QDRANT_DATA_PATH`, `QDRANT_SNAPSHOTS_PATH` (contoh ada di README folder ini)

4. Start Qdrant:

- `docker compose up -d`
- Ikuti log: `docker compose logs -f`

5. Health check dari host:

- `curl -fsS http://localhost:6333/readyz`

Catatan:

- Hostname di network adalah `qdrant`. Kontainer lain di network `ragnet` bisa mengakses via `http://qdrant:6333`.

---

## (Opsional) Menjalankan n8n

1. Pastikan network `ragnet` sudah ada: `docker network create ragnet`
2. `cd infrastructure/n8n`
3. Sesuaikan `.env` (port, basic auth, dll.)
4. Jalankan: `docker compose up -d`
5. UI: `http://localhost:5678`

Di `docker-compose.yml` n8n sudah ada `QDRANT_URL=http://qdrant:6333` untuk akses dalam network yang sama.

---

## Menyiapkan Virtualenv dan Dependency

1. Dari root repo:

- `python3 -m venv .venv`
- `source .venv/bin/activate`

2. Instal paket Python yang diperlukan:

```
pip install -U \
  langchain \
  langchain-qdrant \
  langchain-ollama \
  langchain-core \
  langchain-text-splitters \
  qdrant-client \
  python-dotenv \
  rich \
  pyyaml
```

---

## Ingest Korpus ke Qdrant

1. Pastikan Ollama dan Qdrant aktif.
2. Dari root repo, jalankan:

- `python ingest.py`

Output akan menampilkan jumlah chunk yang terindeks ke koleksi `kb_global` (default). Folder korpus ada di `./corpus/`.

---

## Bertanya (Quickstart)

- `python ask.py "Apa itu App Router di Next.js?"`

Skrip akan mengambil konteks dari Qdrant dan menjawab singkat, hanya berdasarkan dokumen yang ada.

---

## CLI Lanjutan: `call_agent.py`

Fitur:

- Skoring relevansi dengan ambang sederhana
- Profil pencarian dengan fallback heuristik
- Ringkasan sumber dan waktu eksekusi

Contoh penggunaan:

- `python cli/call_agent.py -p nextjs15-en -q "Bagaimana cara menggunakan generateMetadata?"`
- Tanpa profil (semua korpus): `python cli/call_agent.py -q "Apa itu CQRS di NestJS?"`

Profil didefinisikan di `profiles.yaml`:

- `nextjs15-en`, `nestjs11-en`, dan `all` (tanpa filter)

---

## Struktur Penting

- `infrastructure/qdrant/` — Compose dan data Qdrant
- `infrastructure/n8n/` — Compose n8n (opsional)
- `corpus/` — Dokumen sumber (Next.js 15, NestJS 11)
- `ingest.py` — Ingest dokumen → Qdrant
- `ask.py` — Tanya jawab cepat
- `cli/call_agent.py` — CLI dengan profil dan skoring
- `profiles.yaml` — Definisi profil pencarian

---

## Troubleshooting

- Qdrant belum siap:
  - Cek health: `curl -fsS http://localhost:6333/readyz`
  - Lihat log: `cd infrastructure/qdrant && docker compose logs -f`
- Ollama model tidak ada:
  - Jalankan: `ollama pull llama3.1:8b` dan `ollama pull nomic-embed-text`
  - Pastikan server hidup: `ollama serve`
- Port bentrok Docker:
  - Ubah port di `.env` masing-masing folder Compose, lalu `docker compose up -d` ulang
- Ingest gagal konek Qdrant:
  - Pastikan `QDRANT_URL` di root `.env` menunjuk ke `http://localhost:6333`
  - Jika menjalankan dari kontainer lain di `ragnet`, gunakan `http://qdrant:6333`
- Koleksi tidak ditemukan:
  - Pastikan `QDRANT_COLLECTION` di `.env` sesuai dengan yang dipakai saat ingest (`kb_global` default)

---

## Perintah Ringkas

- `docker network create ragnet`
- `cd infrastructure/qdrant && docker compose up -d`
- `source .venv/bin/activate && pip install -U ...`
- `python ingest.py`
- `python ask.py "pertanyaan Anda"`
- `python cli/call_agent.py -p nextjs15-en -q "pertanyaan"`

Selamat mencoba! Jika perlu otomatisasi workflow, lihat README di `infrastructure/n8n` untuk integrasi dengan Qdrant lewat `ragnet`.
