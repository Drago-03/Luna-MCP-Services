"""Vercel serverless entry wrapping FastAPI app.

Provides `app` ASGI callable for serverless runtime. We dynamically load the
implementation from the dash directory `mcp-bearer-token/`.
"""

import runpy
import pathlib

module_path = pathlib.Path(__file__).resolve().parent.parent / "mcp-bearer-token" / "luna_mcp.py"
globals_dict = runpy.run_path(str(module_path))
app = globals_dict["app"]  # type: ignore
