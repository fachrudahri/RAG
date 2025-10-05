# n8n (Automation/Workflow)

Guide to run n8n and integrate with Qdrant via the shared `ragnet` network.

## 1) Create shared Docker network (optional but recommended)

If not present:

```
docker network create ragnet
```

Purpose: containers across folders can access each other (e.g., n8n to Qdrant).

## 2) Run n8n

```
cd infrastructure/n8n

docker compose up -d
# Follow logs until ready
docker compose logs -f

# Stop and clean up when needed
docker compose down
```

Notes:

- This compose uses `.env` for version and port. Ensure these are set: `N8N_VERSION`, `N8N_PORT`, `N8N_BASIC_AUTH_ACTIVE`, `N8N_SECURE_COOKIE`, `GENERIC_TIMEZONE`, `N8N_DATA_PATH`.
- To access Qdrant from n8n over the same network, use `QDRANT_URL=http://qdrant:6333` (already shown in `docker-compose.yml`).
- Data volume persists in `data/`; there’s an optional mount to the repo root—adjust as you prefer.

## 3) Access UI from host

- UI: `http://localhost:5678`

If basic auth is enabled (`N8N_BASIC_AUTH_ACTIVE=true`), ensure credentials in `.env` match your configuration.

## 4) Integrating with Qdrant

- Ensure Qdrant runs on `ragnet`.
- In-network endpoint: `http://qdrant:6333`.
- From host: `http://localhost:6333` (HTTP), `localhost:6334` (gRPC).

## 5) Quick troubleshooting

- Port conflicts? Change `N8N_PORT` in `.env`, then `docker compose up -d` again.
- Missing network? Run `docker network create ragnet` before `docker compose up -d`.
- Check status: `docker compose ps` and `docker compose logs -f`.
