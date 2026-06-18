"""FastAPI server for the RFP Agent web UI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.bedrock_agent import BedrockAgent
from src.config import get_settings
from src.docx_export import export_rfp_to_docx
from src.domains import DOMAIN_BY_ID, DOMAINS
from src.dynamodb_store import DynamoDBStore
from src.validator import validate_rfp_markdown
from src.generation import generate_rfp_with_validation
import os
import time
from collections import deque, defaultdict
from typing import Tuple, Optional
try:
    import jwt
except Exception:
    jwt = None
try:
    import redis
except Exception:
    redis = None

app = FastAPI(title="RFP Generator Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "rfps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_settings = get_settings()
_store = DynamoDBStore(_settings)
_agent = BedrockAgent(_settings)


# Token-role auth and in-memory rate limiter
# VALID_TOKENS env var format: token1[:role],token2[:role]
# e.g. "abc123:admin,def456:reviewer,ghi789" (default role is 'user')
_VALID_TOKENS_RAW = os.getenv("VALID_TOKENS", "")
VALID_TOKENS: dict[str, str] = {}
for part in [p.strip() for p in _VALID_TOKENS_RAW.split(",") if p.strip()]:
    if ":" in part:
        token, role = part.split(":", 1)
        VALID_TOKENS[token] = role
    else:
        VALID_TOKENS[part] = "user"

# JWT config: prefer JWT validation when public key or secret is set
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

# Redis config for production-grade rate limiting
REDIS_URL = os.getenv("REDIS_URL")
from typing import Any as _Any
_redis_client: Optional[_Any] = None
if REDIS_URL and redis:
    try:
        _redis_client = redis.from_url(REDIS_URL)
    except Exception:
        _redis_client = None

# Rate limit: requests per minute per token (or per-IP if no token)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def _get_request_key(request: Request) -> Tuple[str, str]:
    """Return (key, role) where key is token/ip and role is resolved.

    Resolves JWT tokens (if present and valid) first, then API tokens.
    """
    # try JWT from Authorization header
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
        try:
            payload = None
            if JWT_PUBLIC_KEY:
                payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
            elif JWT_SECRET:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload:
                role = payload.get("role", "user")
                sub = payload.get("sub") or payload.get("user") or token
                return f"jwt:{sub}", role
        except Exception:
            # fallthrough to token-based check
            pass

    # fallback to API key header or query param
    token = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if token:
        role = VALID_TOKENS.get(token, "unknown")
        return token, role

    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}", "anon"


@app.middleware("http")
async def auth_and_rate_limit_middleware(request: Request, call_next):
    # If VALID_TOKENS is configured, require a known token for protected endpoints
    if VALID_TOKENS:
        token = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if not token or token not in VALID_TOKENS:
            raise HTTPException(status_code=401, detail="Unauthorized: missing or invalid token")

    # Rate limiting: prefer Redis-backed limiter when available
    key, role = _get_request_key(request)
    now = int(time.time())
    if _redis_client:
        # use Redis simple sliding window via sorted set
        zkey = f"ratelimit:{key}"
        _redis_client.zremrangebyscore(zkey, 0, now - 60)
        count = _redis_client.zcard(zkey)
        if count >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        _redis_client.zadd(zkey, {str(now): now})
        _redis_client.expire(zkey, 65)
    else:
        # in-memory fallback
        bucket = _rate_buckets[key]
        # purge entries older than 60 seconds
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        bucket.append(now)

    # attach role to request.state for handlers to use
    request.state.token_role = role
    return await call_next(request)


class GenerateRfpRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    domain_id: str
    organization: str = Field(min_length=2, max_length=200)
    project_summary: str = Field(min_length=20)
    budget_range: str = "To be determined"
    timeline: str = "6-12 months"


class CreateRfpRequest(BaseModel):
    title: str
    content: str
    domain_id: Optional[str] = None
    organization: Optional[str] = None


class ProposeRequest(BaseModel):
    company_name: str
    company_profile: str


class ChatRequest(BaseModel):
    message: str


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    return (cleaned[:80] or "RFP") + ".docx"


def _rfp_summary(item: dict[str, Any]) -> dict[str, Any]:
    rfp_id = item["rfp_id"]
    return {
        "rfp_id": rfp_id,
        "title": item["title"],
        "status": item.get("status", "draft"),
        "domain_id": item.get("domain_id"),
        "domain_label": item.get("domain_label"),
        "category": item.get("category"),
        "organization": item.get("organization"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "has_docx": bool(item.get("has_docx")),
        "download_url": f"/api/rfps/{rfp_id}/download" if item.get("has_docx") else None,
    }


@app.on_event("startup")
def startup() -> None:
    try:
        _store.ensure_table()
    except Exception as exc:
        print(f"Warning: DynamoDB table setup failed: {exc}")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/domains")
def list_domains() -> list[dict[str, Any]]:
    return [
        {
            "id": d.id,
            "label": d.label,
            "category": d.category,
            "description": d.description,
            "compliance": d.compliance,
            "typical_systems": d.typical_systems,
        }
        for d in DOMAINS
    ]


@app.get("/api/rfps")
def list_rfps() -> list[dict[str, Any]]:
    return [_rfp_summary(item) for item in _store.list_rfps()]


@app.get("/api/rfps/{rfp_id}")
def get_rfp(rfp_id: str) -> dict[str, Any]:
    item = _store.get_rfp(rfp_id)
    if not item:
        raise HTTPException(status_code=404, detail="RFP not found")
    result = _rfp_summary(item)
    result["content"] = item["content"]
    analysis = _store.get_latest_analysis(rfp_id)
    proposal = _store.get_latest_proposal(rfp_id)
    if analysis:
        result["analysis"] = analysis["analysis"]
    if proposal:
        result["proposal"] = proposal["proposal"]
        result["company_name"] = proposal.get("company_name")
    return result


@app.get("/api/rfps/{rfp_id}/download")
def download_rfp_docx(rfp_id: str) -> FileResponse:
    item = _store.get_rfp(rfp_id)
    if not item:
        raise HTTPException(status_code=404, detail="RFP not found")

    docx_path = OUTPUT_DIR / f"{rfp_id}.docx"
    if not docx_path.exists():
        if not item.get("content"):
            raise HTTPException(status_code=404, detail="Word document not found")
        export_rfp_to_docx(
            item["content"],
            docx_path,
            title=item["title"],
            organization=item.get("organization") or "Organization",
            domain_label=item.get("domain_label"),
            category=item.get("category"),
        )
        _store.set_docx_ready(rfp_id, str(docx_path))

    filename = _safe_filename(item["title"])
    return FileResponse(
        path=str(docx_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@app.post("/api/rfps/generate")
def generate_rfp(body: GenerateRfpRequest) -> dict[str, Any]:
    domain = DOMAIN_BY_ID.get(body.domain_id)
    if not domain:
        raise HTTPException(status_code=400, detail="Unknown domain")

    try:
        content, missing_after = generate_rfp_with_validation(
            _agent, domain, body, max_attempts=2
        )
        if not content or len(content.strip()) < 100:
            raise HTTPException(
                status_code=500,
                detail="Bedrock returned an empty or incomplete RFP. Please try again.",
            )

        item = _store.create_rfp(
            title=body.title,
            content=content,
            domain_id=domain.id,
            domain_label=domain.label,
            category=domain.category,
            organization=body.organization,
        )
        rfp_id = item["rfp_id"]

        docx_path = OUTPUT_DIR / f"{rfp_id}.docx"
        export_rfp_to_docx(
            content,
            docx_path,
            title=body.title,
            organization=body.organization,
            domain_label=domain.label,
            category=domain.category,
        )
        _store.set_docx_ready(rfp_id, str(docx_path))

        # If validation failed after allowed reruns, mark needs_review and attach reason
        if missing_after:
            reason = f"Missing sections: {', '.join(missing_after)}"
            _store.mark_needs_review(rfp_id, reason)

        _store.table.update_item(
            Key={"PK": f"RFP#{rfp_id}", "SK": "METADATA"},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "generated"},
        )
        item["status"] = "generated"
        item["has_docx"] = True

        return _rfp_summary(item) | {"content": content}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RFP generation failed: {exc}",
        ) from exc


@app.post("/api/rfps")
def create_rfp(body: CreateRfpRequest) -> dict[str, Any]:
    domain = DOMAIN_BY_ID.get(body.domain_id) if body.domain_id else None
    item = _store.create_rfp(
        body.title,
        body.content,
        domain_id=domain.id if domain else None,
        domain_label=domain.label if domain else None,
        category=domain.category if domain else None,
        organization=body.organization,
    )
    return _rfp_summary(item)


@app.post("/api/rfps/{rfp_id}/analyze")
def analyze_rfp(rfp_id: str) -> dict[str, Any]:
    item = _store.get_rfp(rfp_id)
    if not item:
        raise HTTPException(status_code=404, detail="RFP not found")
    if not item.get("content"):
        raise HTTPException(status_code=400, detail="RFP has no content to analyze")

    try:
        analysis = _agent.analyze_rfp(item["title"], item["content"])
        _store.save_analysis(rfp_id, analysis)
        return {"analysis": analysis}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc


@app.post("/api/rfps/{rfp_id}/propose")
def propose_rfp(rfp_id: str, body: ProposeRequest) -> dict[str, Any]:
    item = _store.get_rfp(rfp_id)
    if not item:
        raise HTTPException(status_code=404, detail="RFP not found")
    latest_analysis = _store.get_latest_analysis(rfp_id)
    proposal = _agent.generate_proposal(
        title=item["title"],
        content=item["content"],
        company_name=body.company_name,
        company_profile=body.company_profile,
        analysis=latest_analysis["analysis"] if latest_analysis else None,
    )
    _store.save_proposal(rfp_id, body.company_name, proposal)
    return {"proposal": proposal}


@app.get("/api/admin/needs-review")
def list_needs_review() -> list[dict[str, Any]]:
    """Return RFP summaries that are marked for review."""
    items = _store.table.scan(FilterExpression="needs_review = :nr", ExpressionAttributeValues={":nr": True}).get("Items", [])
    return [
        {
            "rfp_id": item.get("rfp_id"),
            "title": item.get("title"),
            "review_reason": item.get("review_reason"),
            "updated_at": item.get("updated_at"),
        }
        for item in items
    ]



@app.post("/api/admin/approve/{rfp_id}")
def approve_rfp(rfp_id: str, request: Request) -> dict[str, Any]:
    """Approve an RFP that was previously marked as needing review.

    Requires a token with role 'reviewer' or 'admin'.
    """
    role = getattr(request.state, "token_role", "anon")
    if role not in ("reviewer", "admin"):
        raise HTTPException(status_code=403, detail="Forbidden: reviewer role required")

    item = _store.get_rfp(rfp_id)
    if not item:
        raise HTTPException(status_code=404, detail="RFP not found")

    # record review in history and update metadata
    approver = request.headers.get("x-approver") or "unknown"
    review_item = _store.record_review(rfp_id, approver, action="approved")

    return {"rfp_id": rfp_id, "approved_by": approver, "role": role, "review_id": review_item["SK"]}


@app.get("/api/rfps/{rfp_id}/chat")
def get_chat(rfp_id: str) -> list[dict[str, str]]:
    if not _store.get_rfp(rfp_id):
        raise HTTPException(status_code=404, detail="RFP not found")
    return [
        {"role": row["role"], "content": row["content"], "created_at": row["created_at"]}
        for row in _store.get_chat_history(rfp_id, limit=50)
    ]


@app.post("/api/rfps/{rfp_id}/chat")
def chat_rfp(rfp_id: str, body: ChatRequest) -> dict[str, str]:
    item = _store.get_rfp(rfp_id)
    if not item:
        raise HTTPException(status_code=404, detail="RFP not found")

    try:
        history_rows = _store.get_chat_history(rfp_id, limit=20)
        history = [{"role": row["role"], "content": row["content"]} for row in history_rows]
        latest_analysis = _store.get_latest_analysis(rfp_id)
        latest_proposal = _store.get_latest_proposal(rfp_id)

        _store.save_message(rfp_id, "user", body.message)
        answer = _agent.chat_about_rfp(
            title=item["title"],
            content=item["content"],
            question=body.message,
            history=history,
            analysis=latest_analysis["analysis"] if latest_analysis else None,
            proposal=latest_proposal["proposal"] if latest_proposal else None,
        )
        _store.save_message(rfp_id, "assistant", answer)
        return {"reply": answer}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {exc}",
        ) from exc
