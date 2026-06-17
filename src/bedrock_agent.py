from __future__ import annotations

from typing import Any

import boto3

from src.config import Settings

SYSTEM_PROMPT = """You are an expert RFP (Request for Proposal) analyst and proposal writer.

Your responsibilities:
1. Analyze RFP documents to extract requirements, deadlines, evaluation criteria, and risks.
2. Generate structured, professional proposal responses aligned with RFP requirements.
3. Answer questions about RFP content with precise, actionable guidance.

Always be thorough, professional, and structured. Use clear headings and bullet points when appropriate.
"""


class BedrockAgent:
    """Amazon Bedrock-powered RFP reasoning agent."""

    def __init__(self, settings: Settings) -> None:
        self.model_id = settings.bedrock_model_id
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def _converse(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = []
        for msg in history or []:
            messages.append(
                {
                    "role": msg["role"],
                    "content": [{"text": msg["content"]}],
                }
            )
        messages.append(
            {"role": "user", "content": [{"text": user_message}]}
        )

        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.3,
            },
        )

        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        texts = [block.get("text", "") for block in content_blocks if "text" in block]
        return "\n".join(texts).strip()

    def analyze_rfp(self, title: str, content: str) -> str:
        prompt = f"""Analyze the following RFP document titled "{title}".

Provide a structured analysis with these sections:
## Executive Summary
## Key Requirements
## Submission Deadlines & Format
## Evaluation Criteria
## Compliance & Mandatory Items
## Risks & Gaps
## Recommended Response Strategy

RFP Document:
---
{content}
---
"""
        return self._converse(prompt)

    def generate_proposal(
        self,
        title: str,
        content: str,
        company_name: str,
        company_profile: str,
        analysis: str | None = None,
    ) -> str:
        analysis_block = ""
        if analysis:
            analysis_block = f"""
Prior RFP Analysis:
---
{analysis}
---
"""

        prompt = f"""Write a complete proposal response for the RFP titled "{title}" on behalf of {company_name}.

Company Profile:
---
{company_profile}
---

{analysis_block}

RFP Document:
---
{content}
---

Structure the proposal with:
## Executive Summary
## Understanding of Requirements
## Proposed Solution & Approach
## Team & Qualifications
## Timeline & Deliverables
## Pricing Approach (placeholder if pricing not specified)
## Compliance Matrix
## Why {company_name}
"""
        return self._converse(prompt)

    def chat_about_rfp(
        self,
        title: str,
        content: str,
        question: str,
        history: list[dict[str, Any]] | None = None,
        analysis: str | None = None,
        proposal: str | None = None,
    ) -> str:
        context_parts = [
            f'RFP Title: "{title}"',
            f"RFP Content:\n---\n{content}\n---",
        ]
        if analysis:
            context_parts.append(f"Latest Analysis:\n---\n{analysis}\n---")
        if proposal:
            context_parts.append(f"Latest Proposal Draft:\n---\n{proposal}\n---")

        context = "\n\n".join(context_parts)
        user_message = f"""Use this RFP context to answer the question.

{context}

Question: {question}
"""
        return self._converse(user_message, history=history)
