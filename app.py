"""Small Flask web app for the RabTech Cloud & DevOps internship tasks.

Endpoints:
  /        -> welcome message (no database required)
  /health  -> health check (no database required, used by Docker HEALTHCHECK)
  /items   -> items backed by PostgreSQL when DATABASE_URL is set,
              with a graceful in-memory fallback otherwise.
"""

import os

from flask import Flask, jsonify

try:
    import psycopg
except ImportError:  # psycopg is optional at import time
    psycopg = None

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

FALLBACK_ITEMS = [
    {"id": 1, "name": "sample-item", "source": "fallback"},
    {"id": 2, "name": "demo-item", "source": "fallback"},
]


def get_items_from_db():
    """Fetch items from PostgreSQL, creating the table if needed."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS items ("
                "id SERIAL PRIMARY KEY, name TEXT NOT NULL)"
            )
            cur.execute("SELECT COUNT(*) FROM items")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO items (name) VALUES (%s), (%s)",
                    ("sample-item", "demo-item"),
                )
                conn.commit()
            cur.execute("SELECT id, name FROM items ORDER BY id")
            rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "source": "postgres"} for r in rows]


@app.route("/")
def index():
    return jsonify(
        message="Hello from the RabTech Cloud & DevOps internship app!",
        service="rabtech-cloud-devops-internship",
    )


@app.route("/health")
def health():
    # Must not touch the database: Docker HEALTHCHECK and CI rely on it.
    return jsonify(status="ok"), 200


@app.route("/items")
def items():
    if DATABASE_URL and psycopg is not None:
        try:
            return jsonify(items=get_items_from_db())
        except Exception:  # fall back gracefully if the DB is unreachable
            app.logger.exception("Database query failed, using fallback")
    return jsonify(items=FALLBACK_ITEMS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
