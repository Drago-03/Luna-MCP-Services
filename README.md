# Luna-MCP-Server

[![CI](https://github.com/Drago-03/Luna-MCP-Services/actions/workflows/ci.yml/badge.svg)](https://github.com/Drago-03/Luna-MCP-Services/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/badge/lint-ruff-blue)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/types-mypy-1f5082)](https://mypy-lang.org/)
[![Security Scan](https://img.shields.io/badge/security-trivy-green)](https://github.com/aquasecurity/trivy-action)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Drago-03/Luna-MCP-Services/main.svg)](https://results.pre-commit.ci/latest/github/Drago-03/Luna-MCP-Services/main)
[![codecov](https://codecov.io/github/Drago-03/Luna-MCP-Services/graph/badge.svg?token=17EXUB01OW)](https://codecov.io/github/Drago-03/Luna-MCP-Services)

> Indie Hub submission for the **Puch AI Hackathon**
> Team: **Indie Hub** • Member: **Mantej Singh** • Server: **Luna MCP Server**

![Logo](public/assets/logo.png)

Thin, production-oriented MCP (Model Context Protocol) HTTP server that:

- Implements the Puch AI MCP contract (single `/mcp` JSON-RPC 2.0 POST endpoint)
- Extends the official [Puch AI MCP Starter](https://github.com/TurboML-Inc/mcp-starter)
- Bridges advanced AI & multimodal workloads to **Luna Services** ([repo](https://github.com/Drago-03/Luna-Services)) — Gemini code generation, voice synthesis, Supabase data, and image transforms
- Ships a developer tool suite (GitHub automation, CI triggers, scaffolding, tests, Docker build, image utilities)
- Auth: Bearer token (strict) + optional GitHub OAuth (future-ready)
- Deploys: local (`uvicorn`), public tunnel (`ngrok`), containerized (`docker-compose`)

---

## Tool Registry (MCP Methods)

| Method            | Type      | Description |
|-------------------|-----------|-------------|
| `code_gen`        | Forwarder | Gemini-style code generation via Luna Services (`/api/ai/code`) with graceful fallback |
| `git_clone`       | Local     | Shallow + partial clone (`--depth 1 --filter=blob:none`) into `./repos/<name>` |
| `ci_trigger`      | Forwarder | Dispatch a GitHub Actions workflow (requires `GITHUB_TOKEN`) |
| `scaffold_project`| Local     | Create a minimal Python package + optional test |
| `run_tests`       | Local     | Execute `pytest -q`; summarizes result |
| `img_bw`          | Local     | Fetch image URL → convert to grayscale (Pillow) → base64 PNG |
| `voice_speak`     | Forwarder | Text-to-audio via Luna Services (`/api/ai/voice`) |
| `bw_remote`       | Forwarder | Remote grayscale transform through Luna Services (`/api/image/bw`) |
| `create_branch`   | GitHub    | Create branch from base ref |
| `commit_file`     | GitHub    | Create/update file (base64 content) |
| `open_pr`         | GitHub    | Open pull request |
| `list_issues`     | GitHub    | Enumerate open issues |

> Acceptance test only depends on: `code_gen`, `git_clone`, `img_bw`

---

## Environment Variables

| Name | Required | Purpose |
|------|----------|---------|
| `AUTH_TOKEN` | Yes | Bearer token expected in `Authorization: Bearer <token>` |
| `LUNA_URL` | No (default) | Upstream Luna Services base URL (default `http://localhost:8000`) |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | No | For optional OAuth extension |
| `GITHUB_TOKEN` | Conditional | Needed for write GitHub APIs & CI triggers |
| `SUPABASE_URL` / `SUPABASE_KEY` | Optional | Passed through for Luna Services usage |
| `NGROK_TOKEN` | Recommended | For public tunneling via docker-compose ngrok service |

Sample file: `.env.example`

---

## Quick Start (Local Dev)

Prereqs:

- Python 3.11+
- `uv` (fast dependency manager) – <https://github.com/astral-sh/uv>
- `git`, `ngrok` (if tunneling), optional Docker

```bash
uv venv
source .venv/bin/activate
uv sync
cp .env.example .env
# Edit .env and set AUTH_TOKEN=your_secret
uvicorn mcp-bearer-token.luna_mcp:app --host 0.0.0.0 --port 8086 --reload

# Programmatic import alternative:
# from mcp_bearer_token import app
```

Public tunnel:

```bash
ngrok http 8086
```

---

## Connect Puch AI MCP Client

Once ngrok URL is live (e.g. `https://abc123.ngrok-free.app`):

```bash
/mcp connect https://abc123.ngrok-free.app/mcp your_secret
```

Test tools:
```bash
/mcp call code_gen '{"prompt":"Write hello world in Rust"}'
/mcp call git_clone '{"url":"https://github.com/tensorflow/tensorflow"}'
/mcp call img_bw '{"image_url":"https://picsum.photos/300"}'
```

All should return a JSON-RPC `result` within 5 seconds.

---

## Docker & Compose

```bash
docker compose up --build
```

Services:

- `mcp`: FastAPI app on `8086`
- `ngrok`: Tunnel container (needs `NGROK_TOKEN`)

---

## Adding a New Tool

1. Open `mcp-bearer-token/luna_mcp.py`
2. Define an async function and decorate:

```python
@tool("echo", "Echo back a message")
async def echo(message: str) -> dict:
	return {"echo": message}
```

1. Return JSON-serializable data only.

---

## Auth Model

1. All `/mcp` calls must include `Authorization: Bearer <AUTH_TOKEN>`
2. GitHub mutations require either:
	- `GITHUB_TOKEN` PAT (scopes: `repo`, `workflow`)
	- Future: OAuth exchange (placeholder in `github_oauth/oauth_config.py`)

Unauthorized calls → HTTP 401 (not JSON-RPC envelope).

---

## Test / Reliability Notes

- `git_clone` uses `--depth 1 --filter=blob:none` for speed (<5s on large repos)
- Basic test suite (`pytest -q`) ensures health endpoint & tool registry presence
- CI runs ruff + mypy + pytest + docker build + Trivy scan
- `code_gen` gracefully falls back to a deterministic sample if upstream unreachable
- `img_bw` enforces network + Pillow decode boundaries (default httpx timeout 20s)
- `run_tests` degrades if `pytest` missing (returns informative result)

---

## Architecture

See: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## References

- Puch AI MCP Starter: <https://github.com/TurboML-Inc/mcp-starter>
- Luna Services Backend: <https://github.com/Drago-03/Luna-Services>
- Puch AI Hackathon: <https://puch.ai/hack>
- Mermaid Live: <https://mermaid.live>

---

## Acceptance Checklist

| Item | Status |
|------|--------|
| Bearer Auth | ✅ |
| Tools: core 6 | ✅ |
| Forwarders to Luna Services | ✅ |
| JSON-RPC shape | ✅ |
| ngrok integration | ✅ |
| docker-compose | ✅ |
| Dockerfile | ✅ |
| Docs + diagrams | ✅ |
| Quickstart script | ✅ |
| Acceptance script | ✅ |
| Basic tests | ✅ |

---

## How to Demo (Condensed)

```bash
bash quickstart.sh
# Copy ngrok URL
/mcp connect https://<ngrok>.ngrok-free.app/mcp my_secret
/mcp call code_gen '{"prompt":"Write hello world in Rust"}'
/mcp call git_clone '{"url":"https://github.com/tensorflow/tensorflow"}'
/mcp call img_bw '{"image_url":"https://picsum.photos/300"}'
./acceptance_test.sh https://<ngrok>.ngrok-free.app my_secret
```

---
