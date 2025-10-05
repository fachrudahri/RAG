# Qdrant (Vector DB)

Panduan menjalankan Qdrant untuk stack RAG bersama n8n. Ikuti urutan langkah di bawah.

## 1) Buat shared Docker network (opsional tapi direkomendasikan)

```
docker network create ragnet
```

Kenapa? Supaya kontainer di folder berbeda tetap bisa saling akses (shared network). Kalau kamu tidak butuh n8n memanggil Qdrant langsung, sebenarnya bisa skip network ini—tapi lebih fleksibel kalau ada.

## 2) Jalankan Qdrant

```
cd infrastructure/qdrant

docker compose up -d
# Ikuti log sampai ready
docker compose logs -f

# Matikan dan bersihkan container bila perlu
docker compose down
```

Catatan:
- Kompose ini memakai `.env` untuk versi, port, dan path data. Pastikan variabel berikut sudah terisi: `QDRANT_VERSION`, `QDRANT_HTTP_PORT`, `QDRANT_GRPC_PORT`, `QDRANT_DATA_PATH`, `QDRANT_SNAPSHOTS_PATH`.
- Volume data ada di `data/` dan `snapshots/` agar persisten.
- Healthcheck default: `GET http://localhost:6333/readyz`.

## 3) Akses dari host

- HTTP: `http://localhost:6333`
- gRPC: `localhost:6334`

Contoh cek kesehatan:

```
curl -fsS http://localhost:6333/readyz
```

## 4) Akses dari kontainer lain di network `ragnet`

- HTTP di dalam network: `http://qdrant:6333`

Nama service/hostname di jaringan adalah `qdrant` (lihat `docker-compose.yml`). Pastikan kontainer lain juga join ke network `ragnet`.

## 5) Struktur folder

- `data/` — penyimpanan koleksi/alias Qdrant
- `snapshots/` — lokasi snapshot koleksi
- `.env` — konfigurasi versi, port, dan path volume
- `docker-compose.yml` — definisi service Qdrant dan network `ragnet`

## 6) Troubleshooting cepat

- Port bentrok? Ubah `QDRANT_HTTP_PORT` atau `QDRANT_GRPC_PORT` di `.env` lalu `docker compose up -d` ulang.
- Network belum ada? Jalankan `docker network create ragnet` sebelum `docker compose up -d`.
- Cek status: `docker compose ps` dan `docker compose logs -f`.