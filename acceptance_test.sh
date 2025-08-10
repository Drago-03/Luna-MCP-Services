#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <base_url> <auth_token>" >&2
  exit 1
fi

BASE_URL="$1" # e.g. https://abc123.ngrok-free.app
TOKEN="$2"

call() {
  local method="$1"; shift
  local params="$1"; shift || true
  local payload
  payload=$(jq -n --arg m "$method" --argjson p "$params" '{jsonrpc:"2.0", id:1, method:$m, params:$p}' 2>/dev/null || true)
  if [ -z "$payload" ]; then
    payload="{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$method\",\"params\":$params}"
  fi
  curl -sS -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -X POST "$BASE_URL/mcp" -d "$payload" | jq '.result // .error'
}

echo "[1/3] code_gen"
TIMEFORMAT='  -> elapsed %3R s'; time call code_gen '{"prompt":"Write hello world in Rust"}'

echo "[2/3] git_clone"
TIMEFORMAT='  -> elapsed %3R s'; time call git_clone '{"url":"https://github.com/tensorflow/tensorflow"}'

echo "[3/3] img_bw"
TIMEFORMAT='  -> elapsed %3R s'; time call img_bw '{"image_url":"https://picsum.photos/200"}'

echo "Done. Each call should be <5s wall time."
