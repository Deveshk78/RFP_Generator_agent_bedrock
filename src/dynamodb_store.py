from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from src.config import Settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DynamoDBStore:
    """Single-table DynamoDB store for RFP documents, proposals, and chat."""

    def __init__(self, settings: Settings) -> None:
        self.table_name = settings.dynamodb_table
        self._dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self._client = boto3.client(
            "dynamodb",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.table = self._dynamodb.Table(self.table_name)

    def ensure_table(self) -> None:
        try:
            self._client.describe_table(TableName=self.table_name)
            return
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ResourceNotFoundException":
                raise

        self._client.create_table(
            TableName=self.table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = self._client.get_waiter("table_exists")
        waiter.wait(TableName=self.table_name)

    def create_rfp(self, title: str, content: str) -> dict[str, Any]:
        rfp_id = str(uuid.uuid4())
        item = {
            "PK": f"RFP#{rfp_id}",
            "SK": "METADATA",
            "entity_type": "rfp",
            "rfp_id": rfp_id,
            "title": title,
            "content": content,
            "status": "draft",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        self.table.put_item(Item=item)
        return item

    def list_rfps(self) -> list[dict[str, Any]]:
        response = self.table.scan(
            FilterExpression="entity_type = :etype",
            ExpressionAttributeValues={":etype": "rfp"},
        )
        items = response.get("Items", [])
        items.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return items

    def get_rfp(self, rfp_id: str) -> dict[str, Any] | None:
        response = self.table.get_item(
            Key={"PK": f"RFP#{rfp_id}", "SK": "METADATA"}
        )
        return response.get("Item")

    def save_analysis(self, rfp_id: str, analysis: str) -> dict[str, Any]:
        timestamp = _now_iso()
        item = {
            "PK": f"RFP#{rfp_id}",
            "SK": f"ANALYSIS#{timestamp}",
            "entity_type": "analysis",
            "rfp_id": rfp_id,
            "analysis": analysis,
            "created_at": timestamp,
        }
        self.table.put_item(Item=item)
        self.table.update_item(
            Key={"PK": f"RFP#{rfp_id}", "SK": "METADATA"},
            UpdateExpression="SET #status = :status, updated_at = :updated",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "analyzed",
                ":updated": timestamp,
            },
        )
        return item

    def get_latest_analysis(self, rfp_id: str) -> dict[str, Any] | None:
        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"RFP#{rfp_id}",
                ":sk": "ANALYSIS#",
            },
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def save_proposal(
        self, rfp_id: str, company_name: str, proposal: str
    ) -> dict[str, Any]:
        timestamp = _now_iso()
        item = {
            "PK": f"RFP#{rfp_id}",
            "SK": f"PROPOSAL#{timestamp}",
            "entity_type": "proposal",
            "rfp_id": rfp_id,
            "company_name": company_name,
            "proposal": proposal,
            "created_at": timestamp,
        }
        self.table.put_item(Item=item)
        self.table.update_item(
            Key={"PK": f"RFP#{rfp_id}", "SK": "METADATA"},
            UpdateExpression="SET #status = :status, updated_at = :updated",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "proposal_generated",
                ":updated": timestamp,
            },
        )
        return item

    def get_latest_proposal(self, rfp_id: str) -> dict[str, Any] | None:
        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"RFP#{rfp_id}",
                ":sk": "PROPOSAL#",
            },
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def save_message(
        self, rfp_id: str, role: str, content: str
    ) -> dict[str, Any]:
        timestamp = _now_iso()
        item = {
            "PK": f"RFP#{rfp_id}",
            "SK": f"MSG#{timestamp}",
            "entity_type": "message",
            "rfp_id": rfp_id,
            "role": role,
            "content": content,
            "created_at": timestamp,
        }
        self.table.put_item(Item=item)
        return item

    def get_chat_history(self, rfp_id: str, limit: int = 20) -> list[dict[str, Any]]:
        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"RFP#{rfp_id}",
                ":sk": "MSG#",
            },
            ScanIndexForward=True,
            Limit=limit,
        )
        return response.get("Items", [])
