from __future__ import annotations

from typing import Any

import boto3
from botocore.config import Config

from src.config import Settings

SYSTEM_PROMPT = """You are an expert RFP (Request for Proposal) analyst and proposal writer.

Your responsibilities:
1. Analyze RFP documents to extract requirements, deadlines, evaluation criteria, and risks.
2. Generate structured, professional proposal responses aligned with RFP requirements.
3. Answer questions about RFP content with precise, actionable guidance.

Always be thorough, professional, and structured. Use clear headings and bullet points when appropriate.
"""

ANALYSIS_SYSTEM_PROMPT = """You are a senior RFP analyst specializing in software procurement.

Produce a comprehensive, actionable analysis in Markdown format with:
- Clear ## section headings
- Bullet lists for requirements and risks
- Markdown tables for evaluation criteria, compliance items, and timelines
- **Bold** labels for priority items (Critical, High, Medium)
- A compliance checklist table
- A risk matrix table (Risk | Impact | Mitigation)

Be specific and reference actual content from the RFP. Never output a wall of unformatted text.
"""

CHAT_SYSTEM_PROMPT = """You are an expert RFP advisor helping users understand and respond to RFP documents.

Format EVERY response in clean Markdown:
- Use ## and ### headings to organize sections
- Use bullet lists and numbered lists (never long unbroken paragraphs)
- Use markdown tables for comparisons, matrices, or checklists
- Use **bold** for key terms and deadlines
- When a visual would help (architecture, workflow, timeline, org chart), include a ```mermaid code block
- When describing UI mockups or diagrams, use mermaid flowchart/sequenceDiagram/gantt syntax

Keep responses scannable and professional. Maximum 3-4 sentences per paragraph.
"""

MAX_CONTEXT_CHARS = 45_000


def _truncate(text: str, limit: int = MAX_CONTEXT_CHARS) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return (
        text[:half]
        + "\n\n---\n*[Middle sections omitted for context length — analyze beginning and end]*\n---\n\n"
        + text[-half:]
    )


class BedrockAgent:
    """Amazon Bedrock-powered RFP reasoning agent."""

    def __init__(self, settings: Settings) -> None:
        self.model_id = settings.bedrock_model_id
        boto_config = Config(
            read_timeout=settings.bedrock_read_timeout,
            connect_timeout=60,
            retries={"max_attempts": 2, "mode": "standard"},
        )
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=boto_config,
        )

    def _converse(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        *,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
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
            system=[{"text": system_prompt or SYSTEM_PROMPT}],
            messages=messages,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": 0.3,
            },
        )

        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        texts = [block.get("text", "") for block in content_blocks if "text" in block]
        result = "\n".join(texts).strip()
        if not result:
            raise RuntimeError("Bedrock returned an empty response. Please try again.")
        return result

    def analyze_rfp(self, title: str, content: str) -> str:
        safe_content = _truncate(content)
        prompt = f"""Analyze the RFP document titled "{title}" and provide actionable procurement insights.

Required sections (use ## headings):

## Executive Summary
2-3 sentence overview of the opportunity.

## Key Requirements
Bullet list of must-have functional and technical requirements.

## Submission Deadlines & Format
Table: | Milestone | Date/Format | Notes |

## Evaluation Criteria
Table: | Criterion | Weight (%) | What evaluators want |

## Compliance & Mandatory Items
Checklist table: | Requirement | Mandatory | Evidence needed |

## Risks & Gaps
Risk matrix table: | Risk | Impact | Likelihood | Mitigation |

## Competitive Insights
What would differentiate a winning proposal.

## Recommended Response Strategy
Numbered action plan for the bidding team.

RFP Document:
---
{safe_content}
---
"""
        return self._converse(
            prompt,
            max_tokens=8192,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
        )

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
{_truncate(content)}
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
        return self._converse(prompt, max_tokens=8192)

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
            f"RFP Content:\n---\n{_truncate(content, 30_000)}\n---",
        ]
        if analysis:
            context_parts.append(f"Latest Analysis:\n---\n{_truncate(analysis, 10_000)}\n---")
        if proposal:
            context_parts.append(f"Latest Proposal Draft:\n---\n{_truncate(proposal, 10_000)}\n---")

        context = "\n\n".join(context_parts)
        user_message = f"""Use this RFP context to answer the question with formatted Markdown.

{context}

Question: {question}
"""
        return self._converse(
            user_message,
            history=history,
            max_tokens=4096,
            system_prompt=CHAT_SYSTEM_PROMPT,
        )

    def generate_rfp_document(
        self,
        *,
        title: str,
        domain_label: str,
        domain_category: str,
        domain_description: str,
        compliance: list[str],
        typical_systems: list[str],
        project_summary: str,
        budget_range: str,
        timeline: str,
        organization: str,
    ) -> str:
        compliance_text = ", ".join(compliance) or "Industry-standard security and privacy"
        systems_text = ", ".join(typical_systems) or "Custom software platform"

        prompt = f"""Draft a comprehensive, enterprise-grade Request for Proposal (RFP) for a software engineering program.

Organization: {organization}
Project Title: {title}
Industry Domain: {domain_label} ({domain_category})
Domain Context: {domain_description}
Typical Systems: {systems_text}
Relevant Compliance: {compliance_text}

Project Summary from buyer:
{project_summary}

Budget Range: {budget_range}
Expected Timeline: {timeline}

Write a DETAILED, publish-ready RFP document (minimum 3,000 words) using markdown headings (## and ###).

Required sections — expand each with specific requirements, bullet lists, and tables where appropriate:

## 1. Introduction & Background
## 2. Project Objectives & Success Criteria
## 3. Scope of Work
### 3.1 Functional Requirements (minimum 10 items)
### 3.2 Technical Requirements (minimum 10 items)
### 3.3 Integration Requirements
### 3.4 Security & Compliance Requirements
## 4. Deliverables & Acceptance Criteria
## 5. Mandatory Vendor Qualifications
## 6. Compliance & Regulatory Requirements ({domain_label}-specific)
## 7. Technical Architecture Expectations
## 8. Data Migration & Cutover (if applicable)
## 9. Implementation Timeline & Milestones
## 10. Project Governance & Reporting
## 11. Service Level Requirements (SLAs)
## 12. Evaluation Criteria (with weighted percentages totaling 100%)
## 13. Submission Instructions, Format & Deadline
## 14. Contract Terms & Conditions
## 15. Appendices (Glossary, RFP Q&A process)

Tailor every section specifically to the {domain_label} domain in {domain_category}.
Include domain-specific compliance frameworks, industry terminology, and realistic software requirements.
Use professional procurement language suitable for enterprise software vendors.
"""
        return self._converse(prompt, max_tokens=8192)
