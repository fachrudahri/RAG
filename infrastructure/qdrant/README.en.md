# Qdrant (Vector DB)

Guide to run Qdrant for a RAG stack alongside n8n. Follow the steps below.

## 1) Create a shared Docker network (optional but recommended)

```
docker network create ragnet
```

Why? Containers in different folders can communicate over the same network. If n8n does not need to call Qdrant directly, you can skip this—but having it is more flexible.

## 2) Run Qdrant

```
cd infrastructure/qdrant

docker compose up -d
# Follow logs until ready
docker compose logs -f

# Stop and clean up when needed
docker compose down
```

Notes:
- This compose uses `.env` for version, ports, and data paths. Ensure variables are set: `QDRANT_VERSION`, `QDRANT_HTTP_PORT`, `QDRANT_GRPC_PORT`, `QDRANT_DATA_PATH`, `QDRANT_SNAPSHOTS_PATH`.
- Persistent volumes are mounted to `data/` and `snapshots/`.
- Healthcheck default: `GET http://localhost:6333/readyz`.

## 3) Access from host

- HTTP: `http://localhost:6333`
- gRPC: `localhost:6334`

Health check example:

```
curl -fsS http://localhost:6333/readyz
```

## 4) Access from other containers in `ragnet`

- In-network HTTP: `http://qdrant:6333`

The service/hostname on the network is `qdrant` (see `docker-compose.yml`). Ensure other containers also join `ragnet`.

## 5) Folder structure

- `data/` — Qdrant collections/aliases storage
- `snapshots/` — snapshots location
- `.env` — version, ports, and volume path configs
- `docker-compose.yml` — Qdrant service definition and `ragnet` network

## 6) Quick troubleshooting

- Port conflicts? Change `QDRANT_HTTP_PORT` or `QDRANT_GRPC_PORT` in `.env` and rerun `docker compose up -d`.
- Network missing? Run `docker network create ragnet` before `docker compose up -d`.
- Check status: `docker compose ps` and `docker compose logs -f`.