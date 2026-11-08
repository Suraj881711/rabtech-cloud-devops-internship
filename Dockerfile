# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
# Install dependencies into a virtual environment that the final
# stage can copy wholesale, keeping build tooling out of the image.
FROM python:3.12-slim AS builder

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: final runtime ----------
FROM python:3.12-slim

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Copy only the prepared virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app.py .

# Run as a non-root user.
RUN groupadd --system appuser && useradd --system --gid appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Container health check against the DB-independent /health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
