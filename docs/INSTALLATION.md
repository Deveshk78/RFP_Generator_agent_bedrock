# Installation

This document walks through setting up the project locally for development.

Prerequisites
- Python 3.10+
- Node.js 18+
- Git
- AWS credentials with access to Bedrock and DynamoDB (for full feature set)

Steps
1. Clone the repository

```bash
git clone https://github.com/Deveshk78/RFP_Generator_agent_bedrock.git
cd RFP_Generator_agent_bedrock
```

2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Web UI

```bash
cd web
npm install
cd ..
```

4. Configuration
See `docs/CONFIGURATION.md` for environment variables and examples.

5. Start services (development quickstart)

```bash
chmod +x start-api.sh start-web.sh start-all.sh
./start-api.sh   # starts the FastAPI backend on :8000
./start-web.sh   # starts the Next.js web UI on :3000
# or run everything
./start-all.sh
```


Troubleshooting
- If Bedrock access fails, confirm your AWS credentials and region.
- If DynamoDB table not found, run the provided table creation script (if available) or create the table name in `DYNAMODB_TABLE`.
