from mcp_bearer_token import TOOL_REGISTRY


def test_required_tools_present():
    required = [
        "code_gen",
        "git_clone",
        "ci_trigger",
        "scaffold_project",
        "run_tests",
        "img_bw",
    ]
    for name in required:
        assert name in TOOL_REGISTRY, f"Missing tool: {name}"
