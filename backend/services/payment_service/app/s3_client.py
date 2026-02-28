import json

import boto3
from botocore.exceptions import ClientError

from shared.utils import setup_logger
from .config import settings

logger = setup_logger(__name__)

_s3_client = None


def init_s3():
    global _s3_client
    _s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",
    )

    try:
        _s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info("S3 bucket '%s' already exists", settings.S3_BUCKET_NAME)
    except ClientError:
        _s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info("Created S3 bucket '%s'", settings.S3_BUCKET_NAME)

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.S3_BUCKET_NAME}/*"],
            }
        ],
    }
    _s3_client.put_bucket_policy(
        Bucket=settings.S3_BUCKET_NAME,
        Policy=json.dumps(policy),
    )
    logger.info("S3 bucket policy set to public read")


def get_s3():
    if _s3_client is None:
        raise RuntimeError("S3 client not initialized")
    return _s3_client


def upload_file(file_bytes: bytes, key: str, content_type: str) -> str:
    s3 = get_s3()
    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    public_url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET_NAME}/{key}"
    logger.info("Uploaded to S3: %s", public_url)
    return public_url
