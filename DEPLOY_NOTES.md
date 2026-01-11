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

## HRMS (Human Resources Management)

### Background
- Starting from ERPNext v15, Human Resources is no longer bundled inside ERPNext.
- HR functionality is provided via a standalone application: HRMS.

### Architecture decision
- This repository (Alfal-Co/frappe_docker) is used **only as a runtime environment**.
- HRMS source code is NOT stored inside this repository.
- HRMS is managed as an independent Git repository to allow:
  - Clear ownership
  - Independent upgrades
  - Safe customization without touching ERPNext core

### Repositories
- Runtime environment:
  https://github.com/Alfal-Co/frappe_docker

- HRMS source code (fork):
  https://github.com/Alfal-Co/hrms

- Upstream HRMS:
  https://github.com/frappe/hrms


### Installation record (container-based)
- No local HRMS repo exists on the mac host at `/Users/mohammadaldossari/projects/hrms`.
- HRMS was installed inside the `backend` container under:
  `/home/frappe/frappe-bench/apps/hrms`
- Commands executed inside the `backend` container:
  - `bench get-app hrms --branch version-15`
  - `echo hrms >> sites/apps.txt`
  - `bench --site localhost install-app hrms`
  - `bench --site localhost migrate`

### Local installation status
- HRMS app installed on site: `localhost`
- Database migrated successfully
- Verified HR objects:
  - Employee DocType exists
  - Leave Application DocType exists
  - HR Workspace visible in UI

### Notes
- `sites/apps.txt` includes `hrms` as a registered app.
- No modifications were made to upstream ERPNext source code.
- Future HR customizations must be done in `Alfal-Co/hrms`.
