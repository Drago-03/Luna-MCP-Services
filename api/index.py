"""Vercel serverless entry wrapping FastAPI app.

Vercel discovers a module-level `app` ASGI callable.
We reuse the existing application from the bearer token server.
"""

from importlib import import_module

# Directory is named `mcp-bearer-token`; Python cannot import hyphens directly.
# The module is exposed via implicit namespace when installed, so we fallback to relative path import.
spec = (
    import_module("mcp_bearer_token.luna_mcp") if False else None
)  # placeholder to satisfy linters

try:
    from mcp_bearer_token.luna_mcp import app as app  # type: ignore
except ModuleNotFoundError:
    # Fallback: dynamic import via runpy if package name differs at runtime.
    import runpy
    import pathlib

    module_path = (
        pathlib.Path(__file__).resolve().parent.parent / "mcp-bearer-token" / "luna_mcp.py"
    )
    globals_dict = runpy.run_path(str(module_path))
    app = globals_dict["app"]  # type: ignore
