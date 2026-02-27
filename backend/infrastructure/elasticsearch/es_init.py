"""
One-shot script that seeds Elasticsearch indices from PostgreSQL data.
Reads active shows and venues from PG and bulk-indexes them into ES.
"""

import os
import sys
import time

import psycopg2
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ticketshow:ticketshow123@localhost:5432/ticketshow",
)
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")

SHOWS_INDEX = "shows"
VENUES_INDEX = "venues"

SHOWS_MAPPING = {
    "mappings": {
        "properties": {
            "title": {"type": "text", "analyzer": "standard"},
            "description": {"type": "text", "analyzer": "standard"},
            "duration_minutes": {"type": "integer"},
            "price": {"type": "integer"},
            "language": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "rating": {"type": "keyword"},
            "status": {"type": "keyword"},
        }
    }
}

VENUES_MAPPING = {
    "mappings": {
        "properties": {
            "name": {"type": "text", "analyzer": "standard"},
            "location": {"type": "text", "analyzer": "standard"},
            "city": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "opening_time": {"type": "keyword"},
            "closing_time": {"type": "keyword"},
            "status": {"type": "keyword"},
        }
    }
}


def wait_for_es(es: Elasticsearch, retries: int = 30, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            if es.ping():
                print(f"[es-init] Elasticsearch is ready (attempt {attempt})")
                return
        except Exception:
            pass
        print(f"[es-init] Waiting for Elasticsearch... ({attempt}/{retries})")
        time.sleep(delay)
    print("[es-init] ERROR: Elasticsearch not reachable after retries", file=sys.stderr)
    sys.exit(1)


def create_index(es: Elasticsearch, index_name: str, mapping: dict):
    if es.indices.exists(index=index_name):
        print(f"[es-init] Deleting existing index '{index_name}'")
        es.indices.delete(index=index_name)
    es.indices.create(index=index_name, body=mapping)
    print(f"[es-init] Created index '{index_name}'")


def fetch_shows(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, description, duration_minutes, price, language, rating, status
            FROM events.shows
            WHERE status = 'ACTIVE'
            """
        )
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def fetch_venues(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, name, location, city, opening_time, closing_time, status
            FROM events.venues
            WHERE status = 'ACTIVE'
            """
        )
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    results = []
    for row in rows:
        doc = dict(zip(columns, row))
        # Convert time objects to strings for ES
        for field in ("opening_time", "closing_time"):
            if doc.get(field) is not None:
                doc[field] = str(doc[field])
        results.append(doc)
    return results


def index_documents(es: Elasticsearch, index_name: str, docs: list[dict]):
    actions = [
        {
            "_index": index_name,
            "_id": doc["id"],
            "_source": {k: v for k, v in doc.items() if k != "id"},
        }
        for doc in docs
    ]
    success, errors = bulk(es, actions, raise_on_error=False)
    print(f"[es-init] Indexed {success} documents into '{index_name}' ({len(errors)} errors)")
    if errors:
        for err in errors[:5]:
            print(f"  Error: {err}", file=sys.stderr)


def main():
    print("[es-init] Starting Elasticsearch seeder")
    print(f"[es-init] PG: {DATABASE_URL}")
    print(f"[es-init] ES: {ELASTICSEARCH_URL}")

    es = Elasticsearch(ELASTICSEARCH_URL)
    wait_for_es(es)

    # Connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    try:
        shows = fetch_shows(conn)
        venues = fetch_venues(conn)
    finally:
        conn.close()

    print(f"[es-init] Fetched {len(shows)} shows, {len(venues)} venues from PG")

    # Create indices and index data
    create_index(es, SHOWS_INDEX, SHOWS_MAPPING)
    create_index(es, VENUES_INDEX, VENUES_MAPPING)

    if shows:
        index_documents(es, SHOWS_INDEX, shows)
    if venues:
        index_documents(es, VENUES_INDEX, venues)

    # Refresh indices to make documents immediately searchable
    es.indices.refresh(index=SHOWS_INDEX)
    es.indices.refresh(index=VENUES_INDEX)

    print("[es-init] Indexing complete ✓")


if __name__ == "__main__":
    main()
