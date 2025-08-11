#!/usr/bin/env sh
set -euo pipefail

PORT="${PORT:-8086}"

echo "[start.sh] ===== Luna MCP Server Boot =====" >&2
echo "[start.sh] Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >&2
echo "[start.sh] Using PORT=${PORT}" >&2
echo "[start.sh] Python: $(python -V 2>&1)" >&2
echo "[start.sh] Working dir: $(pwd)" >&2
echo "[start.sh] Listing top-level files:" >&2
ls -1 . | head -50 >&2 || true

if [ -z "${AUTH_TOKEN:-}" ]; then
  echo "[start.sh] WARNING: AUTH_TOKEN not set – /mcp endpoint will 500 on auth attempts" >&2
fi

echo "[start.sh] Installed key packages (fast check):" >&2
python - <<'PY'
import pkgutil, sys
mods = ["fastapi","uvicorn","httpx","PIL","supabase","PyGithub"]
for m in mods:
	found = pkgutil.find_loader(m) is not None
	print(f"[dep] {m}: {'OK' if found else 'MISSING'}")
try:
	import fastapi
	print(f"[dep-version] fastapi={fastapi.__version__}")
except Exception as e: # noqa: BLE001
	print("[dep-error] fastapi import failed", e)
PY

echo "[start.sh] Launching uvicorn..." >&2
exec uvicorn mcp-bearer-token.luna_mcp:app --host 0.0.0.0 --port "${PORT}" --no-server-header
