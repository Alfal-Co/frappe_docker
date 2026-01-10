# ERPNext Docker Deploy Notes (Ubuntu VPS)

## Prereqs
- Docker Engine + Docker Compose v2
- Ports 80/443 open in firewall
- A DNS A record pointing to the server

## Project layout
- This repo is the official `frappe_docker` clone
- Environment config lives in `.env`
- Persistent data lives in Docker volumes

## Start/stop (same on macOS and Ubuntu)
- Start: `docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.proxy.yaml up -d`
- Logs: `docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.proxy.yaml logs -f`
- Stop: `docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.proxy.yaml down`

## First-time site creation (run once)
- `docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.proxy.yaml exec -T backend \
  bench new-site --mariadb-user-host-login-scope=% --db-root-password <DB_PASSWORD> --admin-password <ADMIN_PASSWORD> --install-app erpnext <SITE_NAME>`

## What changes for VPS
- Domain + reverse proxy + SSL
- Use `overrides/compose.https.yaml` (or `overrides/compose.traefik-ssl.yaml`) and set `LETSENCRYPT_EMAIL` + `SITES` in `.env`
- Keep `compose.yaml` + `compose.mariadb.yaml` + `compose.redis.yaml` the same

## Backup
- `docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.proxy.yaml exec -T backend \
  bench --site <SITE_NAME> backup --with-files`
