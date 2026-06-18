<p align="left">
    <img src="assets/icon.svg" alt="RFP Generator Agent" width="120" />
    <a href="https://github.com/Deveshk78/RFP_Generator_agent_bedrock/actions/workflows/ci.yml"><img src="https://github.com/Deveshk78/RFP_Generator_agent_bedrock/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
    <img src="https://img.shields.io/github/license/Deveshk78/RFP_Generator_agent_bedrock" alt="License" />
    <a href="https://github.com/Deveshk78/RFP_Generator_agent_bedrock/releases"><img src="https://img.shields.io/github/v/release/Deveshk78/RFP_Generator_agent_bedrock?label=release" alt="Release"/></a>
    <a href="https://github.com/Deveshk78/RFP_Generator_agent_bedrock/actions/workflows/pages.yml"><img src="https://img.shields.io/github/pages-deploy-status/Deveshk78/RFP_Generator_agent_bedrock" alt="Pages"/></a>
</p>

# RFP Generator Agent (Amazon Bedrock + DynamoDB)

AI-powered **Request for Proposal (RFP)** generator for software engineering programs across multiple industry domains. Built with **Amazon Bedrock** (Claude), **DynamoDB**, **FastAPI**, and a responsive **Next.js** web UI (Tailwind + shadcn/ui).

**Repository:** [github.com/Deveshk78/RFP_Generator_agent_bedrock](https://github.com/Deveshk78/RFP_Generator_agent_bedrock)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Industry Domains](#industry-domains)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Web UI Guide](#web-ui-guide)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## Features

| Feature | Description |
|---------|-------------|
| **Domain RFP Generation** | Generate detailed, domain-specific RFP documents via Bedrock |
| **Word Export** | Auto-export formatted `.docx` files with cover page and sections |
| **RFP Analysis** | Extract requirements, compliance checklists, risk matrices, evaluation criteria |
| **Proposal Drafting** | Generate vendor proposal responses from company profile |
| **AI Chat** | Formatted Markdown answers, Mermaid diagrams, voice input |
| **Persistence** | DynamoDB single-table design for RFPs, analysis, proposals, chat history |
| **Responsive UI** | Laptop, tablet, iPhone, and Android layouts (Tailwind + shadcn) |
| **CLI** | Full command-line interface for scripting and automation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User (Browser / CLI)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
┌─────────────────┐                   ┌─────────────────┐
│  Next.js Web UI │                   │  rfp-agent CLI  │
│  (port 3000)    │                   │  (main.py)      │
└────────┬────────┘                   └────────┬────────┘
         │ /api/* proxy                         │
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                │
└────────┬───────────────────────────────┬────────────────────┘
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│ Amazon Bedrock  │             │   DynamoDB      │
└─────────────────┘             └─────────────────┘
         ▼
┌─────────────────┐
│ output/rfps/    │  ← Generated .docx files
└─────────────────┘
```

### DynamoDB Single-Table Design

| PK | SK | Purpose |
|----|-----|---------|
| `RFP#{uuid}` | `METADATA` | RFP document, title, status, domain |
| `RFP#{uuid}` | `ANALYSIS#{timestamp}` | AI analysis results |
| `RFP#{uuid}` | `PROPOSAL#{timestamp}` | Generated proposals |
| `RFP#{uuid}` | `MSG#{timestamp}` | Chat message history |

---

## Industry Domains

13 pre-built templates: Oil & Gas, Solar, Battery, Wave, Water, Wind, Legal Analytics, Healthcare, Hospitals, Hotels, Trading, Banking, Finance.

---

## Prerequisites

- Python 3.10+
- Node.js 18+ (web UI)
- AWS account with Bedrock + DynamoDB access

---

## Installation

```bash
git clone https://github.com/Deveshk78/RFP_Generator_agent_bedrock.git
cd RFP_Generator_agent_bedrock

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd web && npm install && cd ..
cp .env.example .env
cp web/.env.local.example web/.env.local
```

---

## Configuration

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
BEDROCK_READ_TIMEOUT=600
DYNAMODB_TABLE=RfpAgent
```

---

## Running the Application

```bash
chmod +x start-all.sh start-api.sh start-web.sh rfp-agent
./start-all.sh
```

Open **http://localhost:3000**

---

## Web UI Guide

| Page | Description |
|------|-------------|
| `/` | Domain gallery + recent RFPs |
| `/generate` | Create domain-specific RFP + Word download |
| `/rfp/[id]` | Document, Analysis, Proposal, Chat tabs |

**Chat:** Markdown formatting, Mermaid diagrams, voice input (mic button).

---

## CLI Reference

```bash
./rfp-agent init
./rfp-agent create --title "..." --file samples/rfp.txt
./rfp-agent list
./rfp-agent analyze --rfp-id <uuid>
./rfp-agent propose --rfp-id <uuid> --company "Acme" --profile-file samples/company_profile.txt
./rfp-agent chat --rfp-id <uuid>
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/domains` | Industry domains |
| GET | `/api/rfps` | List RFPs |
| POST | `/api/rfps/generate` | Generate RFP + docx |
| POST | `/api/rfps/{id}/analyze` | Analyze RFP |
| POST | `/api/rfps/{id}/propose` | Generate proposal |
| POST | `/api/rfps/{id}/chat` | Chat |
| GET | `/api/rfps/{id}/download` | Download .docx |

---

## Project Structure

```
├── api/server.py          # FastAPI backend
├── src/                   # Bedrock agent, DynamoDB, docx export, domains
├── web/                   # Next.js + Tailwind + shadcn UI
├── main.py                # CLI
├── rfp-agent              # CLI launcher
├── start-all.sh           # Run everything
└── samples/               # Sample files
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| Load failed | Run `./start-api.sh` |
| Bedrock read timeout | Set `BEDROCK_READ_TIMEOUT=900`, restart API |
| Model not found | Use `us.anthropic.claude-sonnet-4-6` inference profile |

---

## Security

- Never commit `.env` or credentials
- Rotate exposed AWS/GitHub credentials immediately
- Use IAM least-privilege in production

---

**Author:** [Deveshk78](https://github.com/Deveshk78)

## AI Agent Compliance

This project implements a focused AI Agent specialized for Request for Proposal (RFP) workflows. Below is a concise compliance summary you can use for audit, documentation, or product pages.

- Agent classification: request-driven AI Agent (CLI + HTTP API) — not an autonomous background planner.
- Core LLM: Amazon Bedrock (via boto3 bedrock-runtime client). Model is configurable via environment settings.
- Agent persona & structure: explicit system prompts enforce RFP analyst behavior, analysis formatting, and chat rules (see `src/bedrock_agent.py`).
- Capabilities (evidence):
    - RFP generation: `generate_rfp_document()` produces publish-ready RFPs tailored to domains.
    - RFP analysis: `analyze_rfp()` extracts requirements, evaluation criteria, risks, and compliance checklists.
    - Proposal drafting: `generate_proposal()` creates vendor proposal drafts from a company profile.
    - Conversational assistant: `chat_about_rfp()` with chat history persisted in DynamoDB.
- Persistence and audit: single-table DynamoDB store (`src/dynamodb_store.py`) records RFP metadata, analyses, proposals, and chat messages with timestamps.
- Artifact export: `.docx` export implemented in `src/docx_export.py` and served by the API (`/api/rfps/{id}/download`).
- Domains and templates: 13+ industry domains in `src/domains.py` (domain-specific compliance and typical systems).
- Controls & safety: prompt/system-level structure, context truncation, Bedrock client timeouts and limited temperature. Errors and empty responses are handled and surfaced as HTTP errors or CLI errors.

Limitations and recommended mitigations:
- No automatic schema validation of generated content (recommended: add post-generation validators or JSON output + JSON Schema checks).
- No production API authentication or rate limiting (recommended: add token/JWT protection and throttling).
- Hallucination/fact-checking is currently manual — add verification passes, or lightweight fact-extraction checks.

If you want, I can add a post-generation validator that enforces required section headings and flags RFPs needing human review (I can implement code + tests and wire it into the API). 

## Screenshots

Quick preview (placeholders). Replace these with real screenshots by saving under `assets/screenshots/`:

![Screenshot 1](assets/screenshots/screenshot-1.svg)

![Screenshot 2](assets/screenshots/screenshot-2.svg)

## Quick start (summary)

1. Create a Python virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Install web deps:

```bash
cd web && npm install && cd ..
```

3. Decode PNG icons (optional):

```bash
./scripts/decode-icons.sh
```

4. Start backend and web UI (development):

```bash
./start-api.sh
./start-web.sh
```

Visit the Docs site (when deployed) at: https://deveshk78.github.io/RFP_Generator_agent_bedrock (or check the Pages badge above).
