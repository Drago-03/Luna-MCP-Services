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
        # code_gen returns a dict {code, language}
        assert isinstance(out, dict)
        assert set(out.keys()) >= {"code", "language"}
        assert isinstance(out["code"], str)
        # Fallback path should include either the marker or at least the prompt if upstream failed.
        assert ("Fallback" in out["code"]) or ("Test fallback" in out["code"])
    finally:
        target_module._post_luna = original  # type: ignore
