import os
import boto3

s3_client = boto3.client(  # type: ignore
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
)


def upload_file_to_s3(file_path: str, bucket_name: str) -> str:
    """
    upload file to s3
    """
    s3_client.upload_file(file_path, bucket_name, file_path)  # type: ignore
    return f"s3://{bucket_name}/{file_path}"
