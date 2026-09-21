"""Primary import facade for Luna MCP Server.

Exposes FastAPI app and tool registry so that tests and external code can simply:
    from luna_mcp_server import app, TOOL_REGISTRY
"""

from __future__ import annotations

from importlib import import_module as _im

_mod = _im("mcp_bearer_token")
app = _mod.app
TOOL_REGISTRY = _mod.TOOL_REGISTRY

__all__ = ["TOOL_REGISTRY", "app"]
