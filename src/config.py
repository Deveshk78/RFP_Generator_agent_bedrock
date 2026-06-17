import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    bedrock_model_id: str
    dynamodb_table: str


def get_settings() -> Settings:
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    if not access_key or not secret_key:
        raise RuntimeError(
            "AWS credentials missing. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY in .env or your environment."
        )

    return Settings(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        bedrock_model_id=os.getenv(
            "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6"
        ),
        dynamodb_table=os.getenv("DYNAMODB_TABLE", "RfpAgent"),
    )
