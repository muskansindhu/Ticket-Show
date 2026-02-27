import json
import mimetypes
import os
import sys
import time
from pathlib import Path

import boto3
import psycopg2
from botocore.exceptions import ClientError

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ticketshow:ticketshow123@localhost:5432/ticketshow",
)
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minioadmin")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "ticket-show-posters")
S3_PUBLIC_URL = os.environ.get("S3_PUBLIC_URL", "http://localhost:9000")
POSTERS_DIR = os.environ.get("POSTERS_DIR", "/app/posters")


def wait_for_minio(s3, retries=30, delay=2.0):
    """Wait until MinIO is reachable."""
    for attempt in range(1, retries + 1):
        try:
            s3.list_buckets()
            print(f"[s3-init] MinIO is ready (attempt {attempt})")
            return
        except Exception:
            pass
        print(f"[s3-init] Waiting for MinIO... ({attempt}/{retries})")
        time.sleep(delay)
    print("[s3-init] ERROR: MinIO not reachable after retries", file=sys.stderr)
    sys.exit(1)


def wait_for_pg(db_url, retries=30, delay=2.0):
    """Wait until PostgreSQL is reachable."""
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print(f"[s3-init] PostgreSQL is ready (attempt {attempt})")
            return
        except Exception:
            pass
        print(f"[s3-init] Waiting for PostgreSQL... ({attempt}/{retries})")
        time.sleep(delay)
    print("[s3-init] ERROR: PostgreSQL not reachable after retries", file=sys.stderr)
    sys.exit(1)


def ensure_bucket(s3):
    """Create the bucket if it doesn't exist and set public read policy."""
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"[s3-init] Bucket '{S3_BUCKET_NAME}' already exists")
    except ClientError:
        s3.create_bucket(Bucket=S3_BUCKET_NAME)
        print(f"[s3-init] Created bucket '{S3_BUCKET_NAME}'")

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{S3_BUCKET_NAME}/*"],
            }
        ],
    }
    s3.put_bucket_policy(Bucket=S3_BUCKET_NAME, Policy=json.dumps(policy))


def upload_posters(s3) -> list[str]:
    """Upload all poster images from POSTERS_DIR to S3. Returns list of public URLs."""
    posters_path = Path(POSTERS_DIR)
    if not posters_path.exists():
        print(f"[s3-init] WARNING: Posters directory not found: {POSTERS_DIR}")
        return []

    image_files = sorted(
        f
        for f in posters_path.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )

    if not image_files:
        print("[s3-init] No poster images found")
        return []

    urls = []
    for img_path in image_files:
        key = f"posters/{img_path.name}"
        content_type, _ = mimetypes.guess_type(str(img_path))

        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=img_path.read_bytes(),
            ContentType=content_type or "image/jpeg",
        )

        url = f"{S3_PUBLIC_URL}/{S3_BUCKET_NAME}/{key}"
        urls.append(url)
        print(f"[s3-init] Uploaded {img_path.name} -> {url}")

    return urls


def assign_posters_to_shows(poster_urls: list[str]):
    """Update active shows in PG with poster URLs (round-robin assignment)."""
    if not poster_urls:
        print("[s3-init] No poster URLs to assign")
        return

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM events.shows WHERE status = 'ACTIVE' ORDER BY id"
            )
            show_ids = [row[0] for row in cur.fetchall()]

        if not show_ids:
            print("[s3-init] No active shows found in PG")
            return

        print(f"[s3-init] Assigning posters to {len(show_ids)} shows")

        with conn.cursor() as cur:
            for i, show_id in enumerate(show_ids):
                poster_url = poster_urls[i % len(poster_urls)]
                cur.execute(
                    "UPDATE events.shows SET poster_url = %s WHERE id = %s",
                    (poster_url, show_id),
                )

        conn.commit()
        print(f"[s3-init] Updated {len(show_ids)} shows with poster URLs")
    finally:
        conn.close()


def main():
    print("[s3-init] Starting S3 poster seeder")
    print(f"[s3-init] S3:  {S3_ENDPOINT_URL}")
    print(f"[s3-init] PG:  {DATABASE_URL}")

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name="us-east-1",
    )

    wait_for_minio(s3)
    wait_for_pg(DATABASE_URL)

    ensure_bucket(s3)
    poster_urls = upload_posters(s3)
    assign_posters_to_shows(poster_urls)

    print("[s3-init] Seeding complete ✓")


if __name__ == "__main__":
    main()
