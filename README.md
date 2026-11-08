# RabTech Cloud & DevOps Internship — Tasks 03 & 04

![CI/CD](https://github.com/Suraj881711/rabtech-cloud-devops-internship/actions/workflows/ci-cd.yml/badge.svg)

A small Python (Flask) web application containerized with a multi-stage
Docker build and shipped through an automated GitHub Actions CI/CD
pipeline. Built for the RabTech Academy Cloud Computing & DevOps
internship:

- **Task 03 — Multi-Stage Docker Containerization & Optimization**
- **Task 04 — Automated CI/CD Pipeline with GitHub Actions**

## Architecture

```
┌────────────────────────────┐        ┌──────────────────────────┐
│  web (Flask + gunicorn)    │ ─────► │  db (PostgreSQL 16)      │
│  multi-stage Docker image  │  SQL   │  named volume: pgdata    │
│  non-root user, /health    │        │  pg_isready healthcheck  │
└────────────────────────────┘        └──────────────────────────┘
        ▲
        │ port 8000
     clients / CI
```

- `app.py` — Flask app:
  - `GET /` — welcome message (no DB needed)
  - `GET /health` — health check (no DB needed; used by the Docker
    `HEALTHCHECK` and safe to poll at any time)
  - `GET /items` — items read from PostgreSQL via `psycopg` when
    `DATABASE_URL` is set, with a graceful in-memory fallback
- `Dockerfile` — multi-stage build. The builder stage installs
  dependencies into a virtual environment; the final `python:3.12-slim`
  stage copies only the venv and the app, runs as a **non-root user**,
  defines a `HEALTHCHECK` against `/health`, and serves with gunicorn.
  The final image is well under the 150 MB target (see `BUILD-LOGS.md`).
- `docker-compose.yml` — orchestrates `web` + `db` (PostgreSQL) with a
  named volume for persistence and health-gated startup
  (`depends_on: condition: service_healthy`).
- `.github/workflows/ci-cd.yml` — GitHub Actions pipeline (see below).

## Run it with Docker Compose

```bash
docker compose up --build
```

Then:

```bash
curl http://localhost:8000/
curl http://localhost:8000/health     # {"status":"ok"}
curl http://localhost:8000/items      # items served from PostgreSQL
```

Stop and remove containers (data survives in the `pgdata` volume):

```bash
docker compose down
```

## Run the tests locally (no Docker needed)

```bash
pip install -r requirements-dev.txt
flake8 app.py tests/
pytest -v
```

## CI/CD pipeline

The `CI/CD` workflow runs on every **push to `main`** and every
**pull request**:

1. **Lint and Test** — Python 3.12, install dependencies, run `flake8`
   linting and the `pytest` unit tests.
2. **Build and Push** (pushes to `main` only, after tests pass) —
   builds the Docker image with Buildx and pushes it to the GitHub
   Container Registry as
   `ghcr.io/<owner>/rabtech-cloud-devops-internship:latest` and
   `:<commit-sha>`, authenticating with the built-in `GITHUB_TOKEN`
   (`packages: write` permission).

See `BUILD-LOGS.md` for the container build and verification record.
