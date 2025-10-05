# n8n (Automation/Workflow)

Panduan menjalankan n8n dan integrasi dengan Qdrant melalui shared network `ragnet`.

## 1) Buat shared Docker network (opsional tapi direkomendasikan)

Jika belum ada:

```
docker network create ragnet
```

Tujuan: kontainer lintas folder bisa saling akses (mis. n8n ke Qdrant).

## 2) Jalankan n8n

```
cd infrastructure/n8n

docker compose up -d
# Ikuti log sampai siap
docker compose logs -f

# Matikan dan bersihkan container bila perlu
docker compose down
```

Catatan:
- Kompose ini memakai `.env` untuk versi dan port. Pastikan variabel berikut sudah terisi: `N8N_VERSION`, `N8N_PORT`, `N8N_BASIC_AUTH_ACTIVE`, `N8N_SECURE_COOKIE`, `GENERIC_TIMEZONE`, `N8N_DATA_PATH`.
- Untuk akses Qdrant dari n8n via HTTP dalam network yang sama, gunakan `QDRANT_URL=http://qdrant:6333` (sudah dicontohkan di `docker-compose.yml`).
- Volume data berada di `data/` agar persisten; ada mount tambahan ke root repo (opsional, sesuaikan preferensi).

## 3) Akses UI dari host

- UI: `http://localhost:5678`

Jika basic auth diaktifkan (`N8N_BASIC_AUTH_ACTIVE=true`), pastikan kredensial di `.env` sesuai konfigurasi yang kamu pakai.

## 4) Integrasi dengan Qdrant

- Pastikan Qdrant sudah jalan di network `ragnet`.
- Endpoint dalam network: `http://qdrant:6333`.
- Dari host: `http://localhost:6333` (HTTP), `localhost:6334` (gRPC).

## 5) Troubleshooting cepat

- Port bentrok? Ubah `N8N_PORT` di `.env`, lalu jalankan `docker compose up -d` kembali.
- Network belum ada? Jalankan `docker network create ragnet` sebelum `docker compose up -d`.
- Cek status: `docker compose ps` dan `docker compose logs -f`.