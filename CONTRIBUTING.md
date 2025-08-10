# Contributing

Thank you for your interest in improving the Luna MCP Server. For questions or security disclosures you can reach the maintainer at: <mantejarora@gmail.com>

## Index

1. Development Environment
2. Pull Request Checklist
3. Tests & Markers
4. Versioning
5. Commit Style
6. Security
7. Contact

## Development Environment

1. Install uv: <https://github.com/astral-sh/uv>
2. Create env & install deps:

```bash
make install
```

1. Install pre-commit hooks:

```bash
make pre-commit
```

1. Run tests:

```bash
make test
```

1. Start dev server:

```bash
make serve
```

## Pull Request Checklist

- Code formatted (ruff format) and lint passes (ruff check).
- Types pass (mypy) for touched modules.
- Tests added/updated; all tests pass.
- No secrets or credentials committed.
- Update docs (README / ARCHITECTURE) if behavior changes.
- Version bumped if public interface changes.

## Tests & Markers

Network dependent tests are marked with `@pytest.mark.network`. Use:

```bash
pytest -m "not network"
```

## Versioning

The current version is stored in `VERSION`. Use semantic versioning (MAJOR.MINOR.PATCH).

## Commit Style

Conventional commits are encouraged (e.g., `feat: add new tool`, `fix: handle timeout`).

## Security

Report vulnerabilities privately (see `SECURITY.md`). Do not open public issues for undisclosed vulnerabilities. Primary contact: <mantejarora@gmail.com>

## Contact

General inquiries / maintainer email: <mantejarora@gmail.com>

---

Happy hacking.
