"""Alias package exposing the FastAPI app & tool registry.

Source file lives in the dash directory `mcp-bearer-token/` which cannot be imported
as a normal package name. We dynamically load it and re-export expected symbols.
"""

from __future__ import annotations

import importlib.util
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_TARGET = _ROOT / "mcp-bearer-token" / "luna_mcp.py"
if not _TARGET.exists():  # pragma: no cover
    raise FileNotFoundError(f"Expected MCP module at {_TARGET}")

spec = importlib.util.spec_from_file_location("luna_mcp_dash", _TARGET)
if spec is None or spec.loader is None:  # pragma: no cover
    raise ImportError("Unable to load luna_mcp module spec")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[arg-type]

app = getattr(mod, "app")
TOOL_REGISTRY = getattr(mod, "TOOL_REGISTRY")
loaded_module = mod  # provide access for advanced tests
__all__ = ["app", "TOOL_REGISTRY", "loaded_module"]
