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

# Simple API key middleware: set API_KEY env var to enable
API_KEY = os.getenv("API_KEY", "")


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if API_KEY:
        key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if not key or key != API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")
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
