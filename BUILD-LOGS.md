# Build & Verification Log — Task 03 (Docker) / Task 04 (CI/CD)

This file records how the container image for this project is built and
verified. The Docker steps below are the verification procedure followed
during repo setup: run them from the repository root on any machine with
Docker installed and compare against the expected outputs shown. The
application-level checks (lint + unit tests) were additionally executed
for real during repo setup — their actual output is pasted in section 5.

---

## 1. Build the image (multi-stage)

```bash
docker build -t rabtech-cloud-devops-internship:latest .
```

Expected: BuildKit resolves the two stages declared in the `Dockerfile`:

- **builder** (`python:3.12-slim`): creates `/opt/venv` and installs
  `requirements.txt` (Flask, gunicorn, psycopg) into it.
- **final** (`python:3.12-slim`): copies only `/opt/venv` and `app.py`,
  creates the non-root `appuser`, sets the `HEALTHCHECK`, and finishes
  with `Successfully tagged rabtech-cloud-devops-internship:latest`.

## 2. Image size check (target: < 150 MB)

```bash
docker images rabtech-cloud-devops-internship
```

Expected output (size varies slightly by base-image patch level, but the
multi-stage slim build lands well under the 150 MB target — the Python
slim base is ~120 MB and the copied venv adds only the app
dependencies):

```
REPOSITORY                          TAG       SIZE
rabtech-cloud-devops-internship     latest    < 150MB
```

## 3. Non-root user check

```bash
docker run --rm rabtech-cloud-devops-internship:latest whoami
```

Expected output:

```
appuser
```

(The image never runs as root: the `Dockerfile` creates `appuser` and
switches to it with `USER appuser` before the `CMD`.)

## 4. Compose stack, health check, and volume persistence

```bash
docker compose up --build -d
docker compose ps          # web: running (healthy), db: running (healthy)
curl http://localhost:8000/health
curl http://localhost:8000/items
```

Expected:

- `db` becomes healthy first (`pg_isready` healthcheck); `web` starts
  only after that (`depends_on: condition: service_healthy`).
- The web container itself reports `(healthy)` once its Docker
  `HEALTHCHECK` against `/health` starts passing.
- `GET /health` returns `{"status":"ok"}`.
- `GET /items` returns items with `"source":"postgres"`, proving the
  app is reading from the PostgreSQL service.

Persistence test — data must survive a container restart because it
lives in the named volume `pgdata`:

```bash
docker compose down        # containers removed, volume kept
docker compose up -d
curl http://localhost:8000/items   # same rows are still returned
docker volume ls                   # <project>_pgdata is listed
```

## 5. Application checks actually run during repo setup (real output)

Environment: Python 3.12.3, dependencies installed from
`requirements-dev.txt` (Flask 3.1.3, pytest 9.2.0, flake8 7.5.0).

Unit tests (`pytest -v`) — **4 passed**:

```
tests/test_app.py::test_index_returns_200 PASSED                   [ 25%]
tests/test_app.py::test_index_payload PASSED                       [ 50%]
tests/test_app.py::test_health_returns_ok PASSED                   [ 75%]
tests/test_app.py::test_items_fallback PASSED                      [100%]

============================== 4 passed in 0.26s ==============================
```

Lint (`flake8 app.py tests/`): no issues reported.

The same lint and test commands run in CI as the **Lint and Test** job
of `.github/workflows/ci-cd.yml`; on pushes to `main` the pipeline then
builds this image and pushes it to `ghcr.io` (see README, "CI/CD
pipeline").
