# moved from subdirectory
import os
import base64
import asyncio
from typing import Dict, Any, List

from github import Github, GithubException

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

_client: Github | None = None


def _client_lazy() -> Github:
    global _client
    if _client is None:
        if GITHUB_TOKEN:
            _client = Github(GITHUB_TOKEN, per_page=100)
        else:
            _client = Github(per_page=100)
    return _client


async def _run_cmd(cmd: List[str], cwd: str | None = None, timeout: int = 600) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"Command timed out: {' '.join(cmd)}")
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {out.decode(errors='replace')}")
    return out.decode(errors="replace")


async def clone_repo(url: str) -> str:
    """Perform shallow + blobless clone for speed."""
    repos_dir = os.path.abspath("repos")
    os.makedirs(repos_dir, exist_ok=True)
    name = url.rstrip("/").split("/")[-1].removesuffix(".git")
    dest = os.path.join(repos_dir, name)
    if os.path.isdir(dest):
        return dest
    await _run_cmd(["git", "clone", "--depth", "1", "--filter=blob:none", url, dest])
    return dest


async def create_branch(owner: str, repo: str, base: str, new_branch: str) -> Dict[str, Any]:
    gh = _client_lazy()
    r = gh.get_repo(f"{owner}/{repo}")
    base_ref = r.get_git_ref(f"heads/{base}")
    try:
        r.create_git_ref(ref=f"refs/heads/{new_branch}", sha=base_ref.object.sha)
    except GithubException as e:
        raise RuntimeError(f"create_branch failed: {e.data}") from e
    return {"branch": new_branch}


async def commit_file(
    owner: str, repo: str, branch: str, path: str, content_b64: str, message: str
) -> Dict[str, Any]:
    gh = _client_lazy()
    r = gh.get_repo(f"{owner}/{repo}")
    try:
        decoded = base64.b64decode(content_b64).decode("utf-8")
    except Exception as e:  # noqa
        raise RuntimeError("Invalid base64 content") from e
    try:
        existing = r.get_contents(path, ref=branch)
        r.update_file(path, message, decoded, existing.sha, branch=branch)
        status = "updated"
    except GithubException:
        r.create_file(path, message, decoded, branch=branch)
        status = "created"
    return {"status": status, "path": path, "branch": branch}


async def open_pr(
    owner: str, repo: str, head: str, base: str, title: str, body: str
) -> Dict[str, Any]:
    gh = _client_lazy()
    r = gh.get_repo(f"{owner}/{repo}")
    pr = r.create_pull(title=title, body=body, head=head, base=base)
    return {"number": pr.number, "url": pr.html_url, "title": pr.title}


async def list_issues(owner: str, repo: str, limit: int) -> Dict[str, Any]:
    gh = _client_lazy()
    r = gh.get_repo(f"{owner}/{repo}")
    issues = r.get_issues(state="open")
    out = []
    for idx, issue in enumerate(issues):
        if idx >= limit:
            break
        out.append(
            {
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
                "labels": [label.name for label in issue.get_labels()],
            }
        )
    return {"issues": out}
