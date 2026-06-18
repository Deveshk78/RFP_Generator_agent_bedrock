# Architecture

High-level overview

- Web UI: Next.js app in `/web` serves the frontend and calls backend APIs under `/api/*`.
- Backend: FastAPI app in `/api` handles Bedrock model calls, DynamoDB persistence, and docx export.
- Agent: `src/bedrock_agent.py` and related modules implement the prompt orchestration and single-table DynamoDB design.
- Output: Generated `.docx` files are stored in `output/rfps/`.

DynamoDB single-table design and keys are documented in the top-level README.

Extending the system
- Add new templates in `src/domains.py` and wire into the frontend `web/lib/domains.ts` if present.
- Add new analysis pipelines in `src/` and expose endpoints in `api/server.py`.
