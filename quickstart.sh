#!/usr/bin/env bash
set -euo pipefail

echo "=== Luna MCP Server Quickstart (Indie Hub) ==="

if ! command -v uv >/dev/null 2>&1; then
  echo "[1/6] Installing uv..."
  pip install --upgrade uv
else
  echo "[1/6] uv present"
fi

echo "[2/6] Creating virtual environment (if missing)..."
uv venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/6] Syncing dependencies..."
uv sync

if [ ! -f .env ]; then
  echo "[4/6] Creating .env from template..."
  cp .env.example .env
  echo "Edit .env and set AUTH_TOKEN before connecting a client."
fi

echo "[5/6] Launching server on :8086 ..."
(uvicorn mcp-bearer-token.luna_mcp:app --host 0.0.0.0 --port 8086 >/dev/null 2>&1 &) 
sleep 2

echo "[6/6] Starting ngrok tunnel (if installed)..."
if command -v ngrok >/dev/null 2>&1; then
  ngrok http 8086
else
  echo "ngrok not installed. Install from https://ngrok.com/download and run:"
  echo "  ngrok http 8086"
fi
