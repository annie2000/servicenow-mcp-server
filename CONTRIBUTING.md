# Contributing to servicenow-mcp-server

Thank you for your interest in contributing! This document explains how to get involved.

---

## Ways to Contribute

- **Bug reports** — Open an issue describing what went wrong, your ServiceNow version, and steps to reproduce
- **Feature requests** — Open an issue describing the new tool or capability you'd like to see
- **Pull requests** — Fix bugs, add new tools, improve documentation

---

## Development Setup

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/your-username/servicenow-mcp-server.git
   cd servicenow-mcp-server
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate       # macOS/Linux
   # venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your ServiceNow credentials:
   ```bash
   cp .env.example .env
   ```

4. Validate your setup before making changes:
   ```bash
   python3 quick_validation.py
   python3 test_mcp_server.py
   ```

---

## Adding a New Tool

All tools live in `server.py` and are registered with the `@mcp.tool()` decorator. To add a new tool:

1. Find the appropriate section in `server.py` (debugging, config, execution, write ops, or utilities).
2. Add your function with the `@mcp.tool()` decorator.
3. Include a clear docstring — Claude uses this to understand when and how to call the tool.
4. Add a corresponding test case in `test_mcp_server.py`.
5. Update the tool count and description in `README.md`.
6. Add an entry to `CHANGELOG.md` under an `[Unreleased]` section.

**Example skeleton:**
```python
@mcp.tool()
def my_new_tool(
    param_one: str = "",
    limit: int = 20
) -> str:
    """
    One-line summary of what this tool does.

    Args:
        param_one: Description of this parameter
        limit: Max number of records to return (default 20)
    """
    # Your implementation here
    url = f"{INSTANCE}/api/now/table/some_table"
    ...
```

---

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Test your changes against a live ServiceNow instance before submitting
- Update `CHANGELOG.md` with your changes under `[Unreleased]`
- Update `README.md` if you add new tools or change setup steps
- Make sure `.env` is **not** included in your commit (it is listed in `.gitignore`)

---

## Reporting Bugs

When filing a bug report, please include:

1. Output of `python3 quick_validation.py`
2. Output of `python3 test_mcp_server.py`
3. Your ServiceNow version (found at `yourinstance.service-now.com/stats.do`)
4. Python version (`python3 --version`)
5. The exact error message or unexpected behavior

---

## Code Style

- Follow existing patterns in `server.py` for consistency
- Use descriptive variable names
- Keep error messages user-friendly — they surface directly in Claude Desktop
- Return strings from all tools (MCP tools must return serializable output)

---

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
