# moved from subdirectory
import os
import asyncio
from typing import Dict, Any

import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

async def _run(cmd: list[str], cwd: str | None = None, timeout: int = 900) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"Timeout running: {' '.join(cmd)}")
    return proc.returncode, out.decode(errors="replace")

async def run_pytest() -> Dict[str, Any]:
    if not any(os.path.exists(p) for p in ("tests", "test")):
        return {"skipped": True, "reason": "No tests directory."}
    try:
        import pytest  # noqa
    except Exception:
        return {"skipped": True, "reason": "pytest not installed (activate dev extras)."}
    code, output = await _run(["pytest", "-q"])
    return {"exit_code": code, "summary": output.splitlines()[-10:], "truncated_output": output[-4000:]}

async def build_docker_image(tag: str) -> Dict[str, Any]:
    code, output = await _run(["docker", "build", "-t", tag, "."])
    return {"exit_code": code, "tag": tag, "tail": output[-1200:]}

async def trigger_workflow(owner: str, repo: str, workflow_file: str, ref: str, inputs: Dict[str, str]) -> Dict[str, Any]:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN required for workflow dispatch.")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    payload = {"ref": ref, "inputs": inputs}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code not in (204, 201):
            raise RuntimeError(f"Workflow dispatch failed {r.status_code}: {r.text}")
    return {"dispatched": True, "workflow": workflow_file, "ref": ref}

async def project_scaffold(name: str, with_tests: bool) -> Dict[str, Any]:
    if os.path.exists(name):
        return {"created": False, "reason": "already exists"}
    os.makedirs(name, exist_ok=True)
    with open(os.path.join(name, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(f'"""Package {name} (auto-generated)."""\n')
    test_file = None
    if with_tests:
        os.makedirs("tests", exist_ok=True)
        test_file = os.path.join("tests", f"test_{name}.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(f"""def test_import_{name}():\n    import {name}  # noqa\n    assert True\n""")
    return {"created": True, "package": name, "test_file": test_file}
