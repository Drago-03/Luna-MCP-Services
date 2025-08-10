# moved from subdirectory

from __future__ import annotations

import os
import json
import re
import time
from collections import defaultdict, deque
from statistics import mean
from typing import Any, Awaitable, Callable, Dict, AsyncGenerator, Deque, List

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from tools.github_tools import (
    clone_repo,
    create_branch,
    commit_file,
    open_pr,
    list_issues,
)
from tools.automation_tools import (
    trigger_workflow,
    run_pytest,
    build_docker_image,
    project_scaffold,
)
from tools.image_tools import fetch_and_bw

load_dotenv()

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
LUNA_URL = os.getenv("LUNA_URL", "http://localhost:8000")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
PUBLIC_TOOLS = {
    t.strip() for t in os.getenv("PUBLIC_TOOLS", "code_gen,validate").split(",") if t.strip()
}

app = FastAPI(title="Luna MCP Server", version="0.1.0")

# CORS for public endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static frontend (if present)
if os.path.isdir("public"):
    app.mount("/static", StaticFiles(directory="public"), name="static")

ToolFunc = Callable[..., Awaitable[Any]]
TOOL_REGISTRY: Dict[str, ToolFunc] = {}
LATENCY_HISTORY: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=500))


def record_latency(name: str, start: float):
    LATENCY_HISTORY[name].append((time.perf_counter() - start) * 1000.0)


def tool(name: str, desc: str):
    def wrap(fn: ToolFunc):
        TOOL_REGISTRY[name] = fn
        fn.__doc__ = (fn.__doc__ or "") + f"\nMCP Tool: {name}\nDescription: {desc}"
        return fn

    return wrap


def _verify(req: Request):
    if not AUTH_TOKEN:
        raise HTTPException(status_code=500, detail="Server not configured with AUTH_TOKEN")
    if req.headers.get("authorization") != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid token")


@app.post("/mcp")
async def mcp_endpoint(body: Dict[str, Any], request: Request):
    _verify(request)
    method = body.get("method")
    params = body.get("params") or {}
    if method not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail="tool_not_found")
    fn = TOOL_REGISTRY[method]
    try:
        t0 = time.perf_counter()
        result = await fn(**params)
        record_latency(method, t0)
    except TypeError as te:
        raise HTTPException(status_code=400, detail=f"Parameter error: {te}")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
    return {"jsonrpc": "2.0", "id": body.get("id"), "result": result}


@app.get("/mcp")
async def mcp_discovery():
    """Lightweight discovery/diagnostic endpoint.

    Some clients may issue a GET (or HEAD) to verify the MCP endpoint exists
    before sending JSON-RPC POST calls. We return a simple JSON structure
    without requiring auth (intentionally) – similar to `public/health` but
    focused on protocol metadata. Does NOT execute tools.
    """
    return {
        "ok": True,
        "endpoint": "/mcp",
        "protocol": "jsonrpc-2.0",
        "methods": ["POST"],
        "public_tools": sorted(PUBLIC_TOOLS),
    }


# -------------------- Public endpoints (no auth) -------------------- #
def _sanitize(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            lk = k.lower()
            if any(bad in lk for bad in ("token", "secret", "auth", "key")):
                continue
            out[k] = _sanitize(v)
        return out
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


@app.get("/public/health")
async def public_health():
    return {"ok": True, "tools": sorted(PUBLIC_TOOLS)}


@app.get("/public/tools")
async def public_tools():
    return {"tools": sorted(PUBLIC_TOOLS)}


@app.get("/public/describe/{tool_name}")
async def public_describe(tool_name: str):
    if tool_name not in PUBLIC_TOOLS:
        raise HTTPException(status_code=403, detail="method_not_public")
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        raise HTTPException(status_code=404, detail="tool_not_found")
    doc = (fn.__doc__ or "").strip().split("MCP Tool:")[0].strip() or "No description available."
    return {"tool": tool_name, "description": doc}


@app.post("/public/execute")
async def public_execute(body: Dict[str, Any]):
    method = body.get("method")
    params = body.get("params") or {}
    if method not in PUBLIC_TOOLS:
        raise HTTPException(status_code=403, detail="method_not_public")
    fn = TOOL_REGISTRY.get(method)
    if not fn:
        raise HTTPException(status_code=404, detail="tool_not_found")
    try:
        t0 = time.perf_counter()
        result = await fn(**params)
        record_latency(method, t0)
    except TypeError as te:  # parameter mismatch
        raise HTTPException(status_code=400, detail=f"parameter_error: {te}") from te
    except Exception as e:  # noqa: BLE001
        # Do not leak stack details publicly
        raise HTTPException(status_code=500, detail="tool_execution_failed") from e
    return {"method": method, "result": _sanitize(result)}


@app.get("/public/stream")
async def public_stream(method: str, params: str | None = None, prompt: str | None = None):
    """Simple Server-Sent Events (SSE) streaming wrapper around a tool.

    Query Parameters:
      - method: name of the public tool
      - params: optional JSON object (string) of parameters
      - prompt: convenience shortcut for code_gen (merged into params if provided)

    Behavior:
      Executes the tool, then streams the textual result in chunks. If the tool
      returns a dict / list, it will be JSON serialized and chunked. This is a
      *simulated* streaming for demo purposes (tool itself is not inherently
      streaming yet) but provides a stable SSE contract for UI integration.
    """
    if method not in PUBLIC_TOOLS:
        raise HTTPException(status_code=403, detail="method_not_public")
    fn = TOOL_REGISTRY.get(method)
    if not fn:
        raise HTTPException(status_code=404, detail="tool_not_found")

    # Parse params JSON if provided
    param_dict: Dict[str, Any] = {}
    if params:
        try:
            param_dict = json.loads(params)
            if not isinstance(param_dict, dict):
                raise ValueError("params must be an object")
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"invalid_params: {e}") from e
    if prompt and "prompt" not in param_dict:
        param_dict["prompt"] = prompt

    async def generate() -> AsyncGenerator[bytes, None]:
        # Start event
        yield b"event: start\n" + f"data: {{\"method\": \"{method}\"}}\n\n".encode()
        try:
            t0 = time.perf_counter()
            # If the tool is streaming capable (exposes _stream attr), iterate
            stream_attr = getattr(fn, "_stream", None)
            if callable(stream_attr):
                acc = []
                stream_iter = stream_attr(**param_dict)
                try:
                    async for token in stream_iter:  # type: ignore[assignment]
                        acc.append(token)
                        payload = json.dumps({"chunk": token})
                        yield b"data: " + payload.encode() + b"\n\n"
                except TypeError:
                    # Not actually async iterable, fallback to direct call
                    acc.append(await fn(**param_dict))
                result = "".join(str(x) for x in acc)
            else:
                result = await fn(**param_dict)
            record_latency(method, t0)
        except TypeError as te:
            yield b"event: error\n" + f"data: {{\"error\": \"parameter_error: {str(te).replace('\\', '')}\"}}\n\n".encode()
            return
        except Exception as e:  # noqa: BLE001
            yield b"event: error\n" + f"data: {{\"error\": \"execution_failed\", \"detail\": \"{str(e).replace('\\', '')[:200]}\"}}\n\n".encode()
            return

        # Normalize to string for chunking
        if isinstance(result, (dict, list)):
            text = json.dumps(_sanitize(result), indent=2)
        else:
            text = str(result)

        # Chunk the text (approx 120 chars per fragment)
        chunk_size = 120
        for i in range(0, len(text), chunk_size):
            frag = text[i : i + chunk_size]
            payload = json.dumps({"chunk": frag, "offset": i})
            yield b"data: " + payload.encode() + b"\n\n"
        # End event
        yield b"event: end\n" + b"data: {\"ok\": true}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # nginx / proxies
    }
    return StreamingResponse(generate(), media_type="text/event-stream", headers=headers)


@app.get("/public/metrics")
async def public_metrics():
    """Return aggregate latency metrics per tool (avg, p95, count)."""
    out: Dict[str, Dict[str, float | int]] = {}
    for tool, hist in LATENCY_HISTORY.items():
        if not hist:
            continue
        arr: List[float] = list(hist)
        arr_sorted = sorted(arr)
        p95 = arr_sorted[min(len(arr_sorted) - 1, int(0.95 * len(arr_sorted)))]
        out[tool] = {
            "count": len(arr),
            "avg_ms": round(mean(arr), 2),
            "p95_ms": round(p95, 2),
        }
    return {"ok": True, "metrics": out}


@app.get("/")
async def index():
    index_path = os.path.join("public", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "Luna MCP Server", "public_tools": sorted(PUBLIC_TOOLS)}


@app.get("/healthz")
async def healthz():
    return {"ok": True, "tool_count": len(TOOL_REGISTRY), "tools": sorted(TOOL_REGISTRY.keys())}


async def _post_luna(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{LUNA_URL}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, json=payload)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream unreachable: {e}") from e
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Upstream {r.status_code}: {r.text[:400]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Invalid JSON from upstream") from e


RUST_HINT = re.compile(r"fn\s+main\s*\(|Cargo.toml", re.IGNORECASE)
PY_HINT = re.compile(r"def\s+\w+\s*\(|import\s+\w+", re.IGNORECASE)
JS_HINT = re.compile(r"function\s+\w+\s*\(|console\.log", re.IGNORECASE)


def _detect_lang(code: str) -> str:
    if RUST_HINT.search(code):
        return "rust"
    if PY_HINT.search(code):
        return "python"
    if JS_HINT.search(code):
        return "javascript"
    if code.strip().startswith("<!DOCTYPE html"):
        return "html"
    if code.strip().startswith("#include "):
        return "cpp"
    return "plaintext"


@tool("code_gen", "Generate code through Luna Services Gemini pipeline with graceful fallback (stream aware)")
async def code_gen(prompt: str) -> Dict[str, Any]:
    """Return generated code and detected language.

    Normal response shape:
      {"code": "...", "language": "python|rust|javascript|..."}
    Fallback always returns deterministic Rust snippet.
    """
    try:
        data = await _post_luna("/api/ai/code", {"prompt": prompt})
        code = data.get("code") if isinstance(data, dict) else None
        if not code:
            code = str(data)
    except Exception:  # noqa: BLE001
        code = (
            "// Fallback (generation unavailable)\n"
            f"// Prompt: {prompt}\n"
            "fn main() { println!(\"Hello, world!\"); }"
        )
    return {"code": code, "language": _detect_lang(code)}


class _CodeGenStreamer:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self._chunks: List[str] | None = None
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):  # type: ignore[override]
        if self._chunks is None:
            result = await code_gen(prompt=self.prompt)  # call once
            code = result.get("code", "") if isinstance(result, dict) else str(result)
            size = 80
            self._chunks = [code[i : i + size] for i in range(0, len(code), size)] or [""]
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk

def code_gen_stream_factory(**kwargs):  # type: ignore[override]
    return _CodeGenStreamer(prompt=kwargs.get("prompt", ""))

setattr(code_gen, "_stream", code_gen_stream_factory)


@tool("voice_speak", "Text-to-speech via Luna Services; returns base64 audio payload")
async def voice_speak(text: str, voice: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"text": text}
    if voice:
        payload["voice"] = voice
    return await _post_luna("/api/ai/voice", payload)


@tool("bw_remote", "Remote grayscale transform through Luna Services")
async def bw_remote(image_url: str) -> str:
    data = await _post_luna("/api/image/bw", {"image_url": image_url})
    return data.get("image_b64", "")


@tool("git_clone", "Shallow clone a public GitHub repository")
async def git_clone(url: str) -> Dict[str, Any]:
    path = await clone_repo(url)
    return {"path": path}


@tool("create_branch", "Create branch from base ref in a repository")
async def create_branch_tool(owner: str, repo: str, base: str, new_branch: str) -> Dict[str, Any]:
    return await create_branch(owner, repo, base, new_branch)


@tool("commit_file", "Create or update (base64) file content on a branch")
async def commit_file_tool(
    owner: str,
    repo: str,
    branch: str,
    path: str,
    content_b64: str,
    message: str,
) -> Dict[str, Any]:
    return await commit_file(owner, repo, branch, path, content_b64, message)


@tool("open_pr", "Open a pull request from head to base")
async def open_pr_tool(
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str = "",
) -> Dict[str, Any]:
    return await open_pr(owner, repo, head, base, title, body)


@tool("list_issues", "List open issues (limited)")
async def list_issues_tool(owner: str, repo: str, limit: int = 20) -> Dict[str, Any]:
    return await list_issues(owner, repo, limit)


@tool("ci_trigger", "Trigger a GitHub Actions workflow via workflow file name")
async def ci_trigger(
    owner: str,
    repo: str,
    workflow_file: str,
    ref: str = "main",
    inputs: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    if not inputs:
        inputs = {}
    return await trigger_workflow(owner, repo, workflow_file, ref, inputs)


@tool("run_tests", "Run pytest (if installed) and return summary")
async def run_tests() -> Dict[str, Any]:
    return await run_pytest()


@tool("build_image", "Build a Docker image from current directory")
async def build_image(tag: str = "luna-mcp:latest") -> Dict[str, Any]:
    return await build_docker_image(tag)


@tool("scaffold_project", "Scaffold a new Python package (with optional tests)")
async def scaffold_project(name: str, with_tests: bool = True) -> Dict[str, Any]:
    return await project_scaffold(name, with_tests)


@tool("img_bw", "Fetch image & convert to grayscale (base64 PNG)")
async def img_bw(image_url: str) -> str:
    return await fetch_and_bw(image_url)


@tool("validate", "Return a fixed validation number in {country_code}{number} format")
async def validate() -> dict:
    """Return server's own number identifier.

    Format: {country_code}{number} (no separators)
    """
    # Provided number: +91-9805763104 -> normalized to +919805763104 or 919805763104
    # Requirement says {country_code}{number}; we'll omit the plus for strict concatenation.
    return {"number": "919805763104"}


# -------------------- Optional OAuth placeholder endpoints -------------------- #
@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8086")
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "scopes_supported": ["basic"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
    }


@app.get("/authorize")
async def oauth_authorize():
    # Placeholder only; real flow would redirect after consent.
    return {"detail": "OAuth authorize placeholder", "ok": False}


@app.post("/token")
async def oauth_token():
    return {"access_token": "placeholder", "token_type": "bearer", "expires_in": 0}
