from pathlib import Path

from mcp_bearer_token import TOOL_REGISTRY
import pytest
import asyncio


@pytest.mark.asyncio
@pytest.mark.network
async def test_git_clone_idempotent(tmp_path: Path, monkeypatch):
    # Run git_clone twice and ensure path persists and not re-cloned (heuristic)
    git_clone = TOOL_REGISTRY["git_clone"]

    # Use a very small public repo to keep runtime low
    repo_url = "https://github.com/octocat/Hello-World"

    # First clone
    result1 = await git_clone(url=repo_url)
    assert "path" in result1
    p1 = Path(result1["path"])  # local path
    assert p1.exists()

    # Second clone should return same path quickly
    result2 = await git_clone(url=repo_url)
    assert result2["path"] == result1["path"]


@pytest.mark.asyncio
async def test_tool_registry_minimum_set():
    required = {"code_gen", "git_clone", "img_bw"}
    assert required.issubset(TOOL_REGISTRY.keys())
