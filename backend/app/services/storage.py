"""
S3-compatible storage abstraction.
Locally uses MinIO. In production, swap endpoint to AWS S3 or Azure Blob via S3 compat.
"""
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging


logger = logging.getLogger(__name__)


def _client(endpoint_url: str | None = None):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url or settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )


def ensure_buckets():
    """Create required buckets if they don't exist. Call at startup."""
    client = _client()
    for bucket in [settings.S3_BUCKET_FLOORPLANS, settings.S3_BUCKET_HEATMAPS]:
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError:
            try:
                client.create_bucket(Bucket=bucket)
                logger.info(f"Created S3 bucket: {bucket}")
            except Exception as e:
                logger.warning(f"Could not create bucket {bucket}: {e}")


def upload_bytes(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = _client()
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def upload_file_obj(bucket: str, key: str, file_obj, content_type: str) -> str:
    client = _client()
    client.upload_fileobj(
        file_obj,
        bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def download_bytes(bucket: str, key: str) -> bytes:
    client = _client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()




#-----------------------------------------------------
#storage para usar la URL pública
def get_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    client = _client(settings.S3_PUBLIC_URL or settings.S3_ENDPOINT_URL)
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
#-----------------------------------------------------

def delete_object(bucket: str, key: str):
    client = _client()
    client.delete_object(Bucket=bucket, Key=key)
