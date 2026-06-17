# RFP Agent

Executable RFP (Request for Proposal) agent powered by **Amazon Bedrock** and **Amazon DynamoDB**.

## Features

- **Store RFPs** in DynamoDB with metadata and status tracking
- **Analyze RFPs** using Bedrock (requirements, deadlines, evaluation criteria, risks)
- **Generate proposals** tailored to your company profile
- **Interactive chat** to ask questions about any stored RFP

## Prerequisites

- Python 3.10+
- AWS account with:
  - **Amazon Bedrock** model access enabled (Claude 3.5 Sonnet recommended)
  - **DynamoDB** permissions to create/read/write tables
  - IAM permissions for `bedrock:Converse` and DynamoDB operations

## Quick Start

1. **Install and configure**

```bash
cd Bedrock001
cp .env.example .env
```

Edit `.env` with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
DYNAMODB_TABLE=RfpAgent
```

2. **Make the launcher executable**

```bash
chmod +x rfp-agent
```

3. **Initialize DynamoDB table**

```bash
./rfp-agent init
```

4. **Create an RFP**

```bash
./rfp-agent create --title "Cloud Migration RFP" --content "We seek a vendor to migrate..."
# or from a file:
./rfp-agent create --title "Cloud Migration RFP" --file ./samples/rfp.txt
```

5. **List and analyze**

```bash
./rfp-agent list
./rfp-agent analyze --rfp-id <uuid-from-create>
```

6. **Generate a proposal**

```bash
./rfp-agent propose \
  --rfp-id <uuid> \
  --company "Acme Corp" \
  --profile "Acme Corp is a cloud consulting firm with 10+ years experience..."
```

7. **Chat about an RFP**

```bash
./rfp-agent chat --rfp-id <uuid>
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Create DynamoDB table if it does not exist |
| `create` | Store a new RFP (`--title`, `--content` or `--file`) |
| `list` | List all stored RFPs |
| `show` | Show full RFP content (`--rfp-id`) |
| `analyze` | Run Bedrock analysis on an RFP |
| `propose` | Generate a proposal draft |
| `chat` | Interactive Q&A session about an RFP |

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  rfp-agent  │────▶│  Amazon Bedrock  │     │   DynamoDB      │
│  CLI (main) │     │  (Converse API)  │     │   RfpAgent      │
└─────────────┘     └──────────────────┘     │   single-table  │
       │                                      └─────────────────┘
       └──────────────────────────────────────────────▶
```

DynamoDB single-table design:
- `RFP#{id} / METADATA` — RFP document
- `RFP#{id} / ANALYSIS#{timestamp}` — analysis results
- `RFP#{id} / PROPOSAL#{timestamp}` — generated proposals
- `RFP#{id} / MSG#{timestamp}` — chat history

## Security

- Never commit `.env` or AWS credentials to version control
- Rotate access keys if they were exposed
- Use IAM roles with least-privilege policies in production

## Alternative: run without launcher

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py init
```
