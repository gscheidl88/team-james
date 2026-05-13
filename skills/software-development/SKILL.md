---
name: software-development
description: "Python scripts, API integration, MCP tools, agent tool patterns, git commit conventions, and security checklist"
agent: Developer
tools_required: [uv, python, git]
wiki_ref: "[[tooling-policy]]"
version: "1.0"
---

# Skill: Software Development

**Category:** Engineering  
**Trigger:** Any coding, architecture, automation, or technical implementation task  
**Owner:** Developer Agent

---

## When to Use This Skill

- Writing scripts or applications
- Designing APIs or data pipelines
- Code review or debugging
- Setting up CI/CD or automation
- Integrating external services / APIs / MCP tools
- Building agent tools or workflows

---

## Standard Development Workflow

```
1. UNDERSTAND  → What exactly needs to be built? Clarify before coding.
2. DESIGN      → Sketch the structure (functions, classes, modules)
3. IMPLEMENT   → Write complete, working code
4. TEST        → At minimum: happy path + one error case
5. DOCUMENT    → README or inline comments where non-obvious
6. HANDOFF     → Leave runnable state with usage example
```

---

## Python Script Template

```python
#!/usr/bin/env python3
"""
{module_name} - {one-line description}

Usage:
    python {filename}.py [args]

Requirements:
    pip install {package1} {package2}
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    pass  # implementation here


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log.error(f"Fatal: {e}")
        sys.exit(1)
```

---

## API Integration Pattern

```python
import httpx
from typing import Any

BASE_URL = "https://api.example.com"

def api_get(endpoint: str, *, token: str, params: dict | None = None) -> Any:
    """Make an authenticated GET request."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()
```

---

## Agent Tool Pattern (MCP-compatible)

```python
def register_tool(name: str, description: str, parameters: dict):
    """Decorator to register a function as an agent tool."""
    def decorator(fn):
        fn._tool_meta = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        return fn
    return decorator


@register_tool(
    name="analyze_file",
    description="Read and summarize a file",
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
)
def analyze_file(path: str) -> str:
    content = Path(path).read_text()
    return f"File has {len(content)} chars, {content.count(chr(10))} lines."
```

---

## Git Commit Convention

```bash
# Format: type(scope): message
git commit -m "feat(analysis): add revenue trend query

Adds monthly revenue trend with YoY comparison.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Types: `feat` | `fix` | `refactor` | `docs` | `chore` | `test`

---

## Security Checklist

- [ ] No secrets in source code — use `.env` + `python-dotenv`
- [ ] All inputs validated / sanitized
- [ ] File paths checked for traversal (`path.resolve()`)
- [ ] Dependencies pinned in `requirements.txt`
- [ ] `.gitignore` includes `.env`, `*.key`, `__pycache__`

---

## Project Structure (Standard)

```
project/
├── src/
│   └── {module}/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
