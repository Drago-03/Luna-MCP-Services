## Luna-MCP-Services: Deploying Your MCP Server for Puch AI Integration

This guide explains how to deploy your MCP server so it can connect seamlessly with Puch AI via `/mcp connect`. Follow the steps below to ensure your server meets all protocol requirements.

---

### Table of Contents

- Overview
- Prerequisites
- Deployment Steps
- MCP Server Requirements
- Example Directory Structure
- Testing Your Deployment
- Troubleshooting
- Resources

---

### Overview

To integrate Luna-MCP-Services with Puch AI, you must deploy a live MCP server endpoint over HTTPS. This endpoint must serve MCP protocol messages, include a `validate` tool for authentication, and (optionally) expose OAuth endpoints.

---

### Prerequisites

- Source code for Luna-MCP-Services (this repository)
- Cloud hosting platform (e.g., Fly.io, Render, Railway, Deta Space, Hugging Face Spaces)
- HTTPS enabled for all endpoints

---

### Deployment Steps

1. **Deploy Your MCP Server**  
   Use Docker (provided `Dockerfile`) or a platform buildpack. Ensure the main MCP endpoint is publicly accessible (e.g., `https://your-domain.com/mcp`).
2. **Expose the MCP Endpoint**  
   The `/mcp` path must accept JSON-RPC 2.0 requests and respond with MCP-compliant results.
3. **Implement the `validate` Tool**  
   Already provided: `validate` returns the server owner's number in `{country_code}{number}` format (e.g. `919805763104`).
4. **Enable HTTPS**  
   Use a platform with automatic TLS (Fly.io / Render / Railway) or place behind a reverse proxy (Caddy / Nginx) with certificates.
5. **(Optional) Add OAuth Endpoints**  
   Placeholder endpoints are included: `/.well-known/oauth-authorization-server`, `/authorize`, `/token`.

---

### MCP Server Requirements

| Requirement | Provided | Notes |
|-------------|----------|-------|
| `/mcp` endpoint | ✅ | JSON-RPC 2.0 POST |
| `validate` tool | ✅ | Returns phone number `919805763104` |
| HTTPS | Via platform | Use any free tier with TLS |
| OAuth endpoints | Placeholder | Extend for real user auth |
| Public tool façade | ✅ | `/public/execute` allowlist |

---

### Example Directory Structure

```
/
├─ mcp-bearer-token/luna_mcp.py   # Core FastAPI app + tools
├─ tools/                         # Tool implementations
├─ public/index.html              # Public console UI
├─ .well-known/ (optional)        # OAuth metadata (served dynamically)
├─ Dockerfile
└─ DEPLOYMENT.md
```

---

### Testing Your Deployment

1. **Health:** `curl https://your-domain.com/healthz` → JSON with tool list.  
2. **Public Health:** `curl https://your-domain.com/public/health` → subset (no auth).  
3. **Validate Tool:**  
   ```bash
   curl -X POST https://your-domain.com/mcp \
     -H "Authorization: Bearer $AUTH_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":1,"method":"validate","params":{}}'
   ```
4. **Public Execute (no auth, allowlisted):**  
   ```bash
   curl -X POST https://your-domain.com/public/execute \
     -H 'Content-Type: application/json' \
     -d '{"method":"validate","params":{}}'
   ```
5. **Puch AI Connect:**  
   ```
   /mcp connect https://your-domain.com/mcp $AUTH_TOKEN
   ```

---

### Free Hosting Options

| Platform | Notes | Command Sketch |
|----------|-------|----------------|
| Fly.io | App + volume + free TLS | `fly launch` → `fly deploy` |
| Render | Web service (Docker) | Connect repo, set start command |
| Railway | One-click, ephemeral | Add ENV vars, deploy automatically |
| Deta Space | Micro for FastAPI | Package and push via Space CLI |
| Hugging Face Spaces | Good for demos | Add `app.py` if needed; uses gunicorn |

---

### Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 unauthorized | Missing / wrong `AUTH_TOKEN` header | Set header `Authorization: Bearer <token>` |
| 404 tool_not_found | Method not registered | Check tool name and spelling |
| 502 upstream errors | Luna Services unreachable | Verify `LUNA_URL` and service health |
| CORS errors | Frontend origin mismatch | CORS already set to `*`; confirm correct URL |

---

### Resources

- Puch AI MCP Integration: https://puch.ai/mcp
- Model Context Protocol Spec: https://modelcontextprotocol.io/specification/
- FastAPI: https://fastapi.tiangolo.com/

---

Deploy, test, connect — your MCP server is ready for Puch AI.
