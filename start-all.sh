#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo "Starting API on http://127.0.0.1:8000 ..."
uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT

if [ ! -d "web/node_modules" ]; then
  echo "Installing web dependencies..."
  (cd web && npm install)
fi

echo "Starting web UI on http://localhost:3000 ..."
echo "Press Ctrl+C to stop both servers."
(cd web && npm run dev)
