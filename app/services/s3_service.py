import logging
import os
from typing import BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class S3Service:
    """Service for uploading files to AWS S3."""

    PRESIGNED_URL_EXPIRATION = 300  # 5 minutes in seconds
    S3_GET_OBJECT = "get_object"

    def __init__(
        self,
        bucket_name: str | None = None,
        region: str | None = None,
    ):
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET", "maintenance-images")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self._client = None

    @property
    def client(self):
        """Lazy initialization of S3 client."""
        if self._client is None:
            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    @staticmethod
    def _get_error_code(error: ClientError) -> str:
        """Extract error code from ClientError."""
        return error.response.get("Error", {}).get("Code", "")

    def _ensure_bucket_accessible(self) -> None:
        """Verify bucket exists and is accessible, create if doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info("Bucket '%s' is accessible", self.bucket_name)
        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "404":
                self._create_bucket()
            else:
                raise

    def _create_bucket(self) -> None:
        """Create S3 bucket with proper region configuration."""
        try:
            if self.region == "us-east-1":
                self.client.create_bucket(Bucket=self.bucket_name)
            else:
                self.client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region}
                )
            logger.info("Successfully created bucket '%s'", self.bucket_name)
        except ClientError as create_error:
            error_code = self._get_error_code(create_error)
            if error_code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
                logger.warning(
                    "Bucket '%s' already exists. Attempting to use it.",
                    self.bucket_name,
                )
            else:
                logger.error(
                    "Failed to create bucket '%s': %s",
                    self.bucket_name,
                    str(create_error),
                )
                raise

    def upload_image(
        self,
        file_content: BinaryIO,
        file_name: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload an image to S3 and return the URL.

        Args:
            file_content: File-like object with the image content
            file_name: Name to save the file as in S3
            content_type: MIME type of the file

        Returns:
            URL of the uploaded image

        Raises:
            S3UploadError: If upload fails
        """
        # Ensure bucket is accessible before attempting upload
        try:
            self._ensure_bucket_accessible()
        except Exception as bucket_error:
            logger.error(
                "Bucket '%s' is not accessible: %s",
                self.bucket_name,
                str(bucket_error),
            )
            raise S3UploadError(
                f"Bucket '{self.bucket_name}' is not accessible: {str(bucket_error)}"
            ) from bucket_error
        
        try:
            self.client.upload_fileobj(
                file_content,
                self.bucket_name,
                file_name,
                ExtraArgs={"ContentType": content_type},
            )

            # Generate presigned URL valid for configured expiration time
            presigned_url = self.client.generate_presigned_url(
                self.S3_GET_OBJECT,
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_name
                },
                ExpiresIn=self.PRESIGNED_URL_EXPIRATION
            )
            logger.info("Successfully uploaded '%s' to S3 with presigned URL", file_name)
            return presigned_url

        except ClientError as e:
            error_code = self._get_error_code(e) or "Unknown"
            logger.error(
                "AWS ClientError uploading '%s': %s - %s",
                file_name,
                error_code,
                str(e),
            )
            raise S3UploadError(f"Failed to upload to S3: {error_code}") from e

        except BotoCoreError as e:
            logger.error(
                "BotoCoreError uploading '%s': %s",
                file_name,
                str(e),
            )
            raise S3UploadError(f"S3 connection error: {str(e)}") from e


class S3UploadError(Exception):
    """Custom exception for S3 upload failures."""

    pass


# Singleton instance for easy import
s3_service = S3Service()
