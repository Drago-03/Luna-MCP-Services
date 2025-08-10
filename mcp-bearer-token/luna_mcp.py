# moved from subdirectory

from __future__ import annotations

import os
from typing import Any, Awaitable, Callable, Dict

import httpx
from fastapi import FastAPI, HTTPException, Request
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

app = FastAPI(title="Luna MCP Server", version="0.1.0")

ToolFunc = Callable[..., Awaitable[Any]]
TOOL_REGISTRY: Dict[str, ToolFunc] = {}


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
        result = await fn(**params)
    except TypeError as te:
        raise HTTPException(status_code=400, detail=f"Parameter error: {te}")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
    return {"jsonrpc": "2.0", "id": body.get("id"), "result": result}


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


@tool("code_gen", "Generate code through Luna Services Gemini pipeline with graceful fallback")
async def code_gen(prompt: str) -> str:
    try:
        data = await _post_luna("/api/ai/code", {"prompt": prompt})
        if "code" in data:
            return data["code"]
        return str(data)
    except HTTPException:
        return f"// Fallback (upstream unavailable)\n// Prompt: {prompt}\nfn main() {{ println!(\"Hello, world!\"); }}"


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
