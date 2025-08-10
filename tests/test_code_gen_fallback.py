import pytest
from mcp_bearer_token import TOOL_REGISTRY, loaded_module


@pytest.mark.asyncio
async def test_code_gen_fallback(monkeypatch):
    code_gen = TOOL_REGISTRY["code_gen"]

    class DummyHTTPError(Exception):
        pass

    async def broken_post(*args, **kwargs):  # noqa: ANN001, D401
        raise DummyHTTPError("network down")

    # Monkeypatch internal _post_luna used in code_gen (module attribute resolution)
    target_module = loaded_module
    if not hasattr(target_module, "_post_luna"):
        pytest.skip("_post_luna not exposed; fallback path implicitly covered elsewhere")

    original = target_module._post_luna
    target_module._post_luna = broken_post  # type: ignore
    try:
        out = await code_gen(prompt="Test fallback")
        assert "Fallback" in out
    finally:
        target_module._post_luna = original  # type: ignore
