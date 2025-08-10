# Basic Copilot Instructions

_File: `.github/instructions/basic-instructions.md`_

These global directives apply to **every** Copilot Chat or Inline session inside the **luna-mcp-server** repository.

---

## 1. Tone & Formatting

- **Professional, concise prose**.
- **No emotes or emojis** under any circumstance.
- Use Markdown for paragraphs, lists and code blocks; avoid decorative styling.
- Prefer complete sentences; no “lol”, “btw”, or chat-style slang.

## 2. Coding Standards

- **Python 3.11** with `black`-compatible formatting (PEP 8).
- Type-annotate public functions.
- Use docstrings (`"""Triple-quoted."""`) on every module, class and function.
- Raise explicit exceptions rather than silent failures.
- Keep third-party imports alphabetised and grouped separately from stdlib imports.

## 3. Repository Context

This project is an AI-powered **MCP server** for the Puch AI Hackathon.
Key folders:

```text
mcp-bearer-token/   # FastAPI entry-point (luna_mcp.py)
tools/              # GitHub ops, CI/CD, image utils
.github/            # Chat modes, CI, issue templates
public/assets/      # Static branding assets (logo.png)
```

## 4. Autonomy Mode

When the developer types the **chat-mode trigger**

```text
/luna-mcp
```

Copilot should switch to _agentic_ behaviour defined in `.github/chatmodes/Luna-MCP.chatmode.md`:

1. Think → Plan → Code → Test → Document → Output.
2. Generate every required file as triple-backtick snippets **in one response**.
3. Run reasoning to ensure import paths resolve.
4. Conclude with `quickstart.sh` and demo guide.

**Do not** ask the user to supply snippets; build everything autonomously.

## 5. Prohibited Content

- No emotes (e.g. 😀, 🚀) or informal gifs.
- No copyrighted text longer than 90 characters.
- No sensitive credentials; use placeholders (`<TOKEN>`).

## 6. External References

Primary upstream projects:

- Puch AI MCP Starter – <https://github.com/TurboML-Inc/mcp-starter>
- Luna Services – <https://github.com/Drago-03/Luna-Services>

When citing them, use plain links—no embeds, images or emotes.

## 7. Completion Checklist (implicit)

- [ ] Follows PEP 8 & project conventions
- [ ] No missing imports
- [ ] No TODO comments in final output
- [ ] No emotes or emojis anywhere
- [ ] Acceptance test logic referenced where relevant

_If a completion would violate any rule above, Copilot must correct itself before responding._
