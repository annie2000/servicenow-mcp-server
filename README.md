# servicenow-mcp-server

> **Connect Claude Desktop to ServiceNow. Diagnose, fix, and manage — through natural conversation.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
[![ServiceNow Vancouver+](https://img.shields.io/badge/ServiceNow-Vancouver%2B-brightgreen.svg)](https://servicenow.com)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects **Claude Desktop** to your **ServiceNow** instance — enabling natural-language management of AI Agents, Agentic Workflows, Flow Designer executions, and system logs.

---

## What Is This?

Two tools. One repository. One story.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   server.py          ←→   Claude Desktop / Claude Code             │
│   MCP Server              Natural language interface                │
│   40+ tools               "Show me all AI agents"                  │
│                           "Why did the last workflow fail?"         │
│                                                                     │
│   admin_bot/         →    Interactive HTML Report                   │
│   healthcheck.py          21 diagnostic checks                      │
│   Run anywhere            Root cause + fix scripts                  │
│   No Claude needed        Grade: EXCELLENT → CRITICAL               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**`server.py`** — MCP server that connects Claude Desktop to your ServiceNow instance. Ask Claude to manage AI agents, debug workflows, and read logs in natural language.

**`admin_bot/`** — Standalone health check tool. Run it before every demo. Get a visual, interactive HTML report with specific fixes — in under 3 minutes.

---

## Diagrams

### Architecture

[![Architecture](https://github.com/annie2000/servicenow-mcp-server/raw/main/docs/images/architecture.svg)](docs/images/architecture.svg)

### How It Works — Execution Flow

[![Execution Flow](https://github.com/annie2000/servicenow-mcp-server/raw/main/docs/images/execution-flow.svg)](docs/images/execution-flow.svg)

### Tool Categories

[![Tool Categories](https://github.com/annie2000/servicenow-mcp-server/raw/main/docs/images/tool-categories.svg)](docs/images/tool-categories.svg)

### Before vs. After

[![Before After](https://github.com/annie2000/servicenow-mcp-server/raw/main/docs/images/before-after.svg)](docs/images/before-after.svg)

---

## Background

### What is ServiceNow?

[ServiceNow](https://www.servicenow.com) is an enterprise cloud platform built around workflow automation and IT service management (ITSM). At its core, it provides a unified system of record for business processes — incidents, change requests, approvals, and more — across IT, HR, security, and customer service teams.

In recent releases (Vancouver, Washington DC, Xanadu), ServiceNow introduced **AI Agent Studio** and the **Now Assist** platform, enabling organizations to build and deploy autonomous AI agents that can reason, plan, and execute multi-step workflows using a growing library of tools. These agents are orchestrated through **Agentic Workflows** (use cases) and backed by LLMs — making them powerful but also complex to debug and manage.

### What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard developed by Anthropic that defines how AI models like Claude connect to external tools and data sources. Think of it as a universal adapter: instead of building one-off integrations for every system, MCP gives any MCP-compatible AI model a standardized way to discover and call tools exposed by an MCP server.

An MCP server is a lightweight process that:

1. Declares a list of **tools** (functions with typed inputs and descriptions)
2. Executes those tools when called by the AI model
3. Returns results back to the model's context

This means Claude can call `list_ai_agents()` or `query_execution_plans()` the same way it reasons about any other information — no custom UI, no manual API calls.

### What is Claude Code?

[Claude Code](https://claude.ai/download) is Anthropic's agentic coding environment that runs Claude directly in your terminal. Unlike the web chat interface, Claude Code can read and write files, execute shell commands, browse the web, and — critically — connect to MCP servers running locally on your machine.

When combined with this MCP server, Claude Code can interact with your ServiceNow instance as a fully autonomous agent: inspecting logs, diagnosing failures, creating or modifying AI agents, and executing multi-step investigations — all from a single terminal session.

### Why use all three together?

ServiceNow's AI Agent platform is powerful but operationally opaque. When an agentic workflow fails, diagnosing the root cause requires jumping between multiple tables (`sn_aia_execution_plan`, `sn_aia_tools_execution`, `sys_generative_ai_log`, `sys_flow_log`) with no unified view. Managing agents — creating, cloning, updating tool configurations — requires navigating the UI or writing REST API calls by hand.

This MCP server closes that gap:

| Without this server | With this server |
|---|---|
| Manually query 5+ tables to debug a failed workflow | Ask Claude: *"Why did the last execution plan fail?"* |
| Write REST API calls to create or clone an agent | Ask Claude: *"Clone the MS Learn Agent and add the web search tool"* |
| Switch between browser tabs to correlate logs | Ask Claude: *"Show me all errors from the last hour across syslog and AI logs"* |
| Require ServiceNow UI expertise to onboard new developers | Any developer with Claude Desktop can inspect and manage agents immediately |

The combination of ServiceNow's agentic platform, MCP's tool protocol, and Claude's reasoning gives developers a conversational interface to a system that was previously only accessible through complex UIs and REST APIs. For SI partners building on ServiceNow's AI capabilities, this dramatically reduces the time to understand, debug, and extend agentic workflows.

---

## Overview

This MCP server exposes **40+ tools** that Claude can call directly, organized into five categories:

| Category | Description | Key Tools |
|---|---|---|
| 🔍 **Debugging** | Query system and AI logs | `query_syslog`, `query_generative_ai_logs`, `query_flow_logs` |
| ⚙️ **AI Agent Config** | Read agents, workflows, tools, triggers | `list_ai_agents`, `get_agent_details`, `list_agentic_workflows` |
| 📊 **Execution Monitoring** | Track agentic workflow runs | `query_execution_plans`, `get_execution_details`, `query_agent_messages` |
| ✍️ **Write Operations** | Full CRUD for agents, workflows, tools, triggers | `create_ai_agent`, `update_ai_agent`, `add_tool_to_agent` |
| 🛠️ **Utilities** | Clone agents, clean up configs | `clone_ai_agent`, `cleanup_agent_configs` |

### Example prompts in Claude Desktop

```
"Show me all active AI agents"
"What errors occurred in the last hour?"
"Create a new AI agent for incident triage"
"Clone the MS Learn Agent and name it IT Support Agent"
"Show me the last 5 execution plans and their status"
"Which tools failed in the most recent agentic workflow run?"
"Do a health check on my instance"
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.9+ | `python3 --version` |
| Claude Desktop | Latest | [Download](https://claude.ai/download) |
| ServiceNow | Vancouver+ | Requires AI Agent Studio plugin |

**ServiceNow roles required:**

| Operation | Role |
|---|---|
| Read logs, agents, workflows | `admin` |
| Create / update / delete agents, workflows, tools, triggers | `sn_aia_admin` |

> ⚠️ `sn_aia_admin` is a **scoped role** — separate from standard admin. You need both for full write access.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/annie2000/servicenow-mcp-server.git
cd servicenow-mcp-server
```

### 2. Create a virtual environment and install dependencies

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:
```
SERVICENOW_INSTANCE=https://yourinstance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### 4. Validate your setup

```bash
python3 quick_validation.py
```

All checks should show ✅. If any fail, see [Troubleshooting](#troubleshooting).

### 5. Configure Claude Desktop

Open Claude Desktop → **Settings** → **Developer** → **Edit Config**.

**macOS** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "servicenow-mcp-server": {
      "command": "/absolute/path/to/servicenow-mcp-server/venv/bin/python",
      "args": ["/absolute/path/to/servicenow-mcp-server/server.py"]
    }
  }
}
```

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "servicenow-mcp-server": {
      "command": "C:\\absolute\\path\\to\\servicenow-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["C:\\absolute\\path\\to\\servicenow-mcp-server\\server.py"]
    }
  }
}
```

> ⚠️ Always use **absolute paths**. Restart Claude Desktop after saving.

When the tools load successfully, you'll see a 🔨 hammer icon in Claude Desktop.

---

## Repository Structure

```
servicenow-mcp-server/
│
├── server.py                    # MCP server — all 40+ tools
├── work_planning_tools.py       # Work Planning Agent tools (register pattern)
├── quick_validation.py          # Pre-flight setup checker (run first)
├── test_connection.py           # Minimal connection test
├── test_detailed.py             # Verbose connection diagnostics
├── test_mcp_server.py           # Full test suite with CRUD validation
├── requirements.txt             # Python dependencies
├── .env.example                 # Credentials template
├── .gitignore
├── LICENSE                      # Apache 2.0
├── CHANGELOG.md
├── CONTRIBUTING.md
│
├── admin_bot/                   # ← NEW: Standalone health check tool
│   ├── healthcheck.py           # Main script — 21 checks + interactive HTML
│   ├── run_healthcheck.sh       # Mac/Linux launcher
│   ├── run_healthcheck.bat      # Windows launcher
│   ├── sn_admin_bot.html        # Browser fallback (CORS limitations apply)
│   ├── .env.template            # Credentials template
│   └── README.md                # Admin Bot quick-start guide
│
└── docs/
    └── images/                  # Architecture diagrams (SVG)
```

---

## Testing

Recommended order:

```bash
# 1. Basic connectivity
python3 test_connection.py

# 2. Pre-flight check (permissions, table access)
python3 quick_validation.py

# 3. Full validation including CRUD cycle
python3 test_mcp_server.py
```

`test_mcp_server.py` creates a temporary test agent, verifies it, updates it, then deletes it — confirming full read/write access end to end.

---

## Tool Reference

### 🔍 Debugging Tools

| Tool | Description |
|------|-------------|
| `query_syslog` | Query system logs with filters for message, source, level, and time window |
| `query_generative_ai_logs` | Query `sys_generative_ai_log` — AI Agent invocations and LLM interactions |
| `query_generative_ai_logs_detailed` | Full field access including request/response payloads and error details |

### 🌊 Flow Designer Tools

| Tool | Description |
|------|-------------|
| `query_flow_contexts` | Query flow execution summaries from `sys_flow_context` |
| `query_flow_logs` | Detailed per-action flow logs from `sys_flow_log` |
| `get_flow_context_details` | Full details for a specific flow execution including all logs |
| `query_flow_reports` | Runtime state data from `sys_flow_report_doc_chunk` |

### ⚙️ AI Agent Configuration Tools

| Tool | Description |
|------|-------------|
| `list_ai_agents` | List all AI agents (active only by default) |
| `get_agent_details` | Get full details for a specific agent including its tools |
| `list_agentic_workflows` | List all agentic workflows / use cases |
| `list_agent_tools` | List all tools available to AI agents, filterable by type |
| `list_trigger_configurations` | List trigger configurations for agentic workflows |

### 📊 Execution Monitoring Tools

| Tool | Description |
|------|-------------|
| `query_execution_plans` | Query agentic workflow execution plans |
| `query_execution_tasks` | Query individual agent tasks within an execution plan |
| `query_tool_executions` | See which tools were called and their results |
| `get_execution_details` | Full execution breakdown including tasks and tool calls |
| `query_agent_messages` | Query agent conversation messages and short-term memory |

### ✍️ Write Operations

| Tool | Description |
|------|-------------|
| `create_ai_agent` | Create a new AI agent with role and instructions |
| `update_ai_agent` | Update an existing agent (partial updates supported) |
| `delete_ai_agent` | Delete an agent (requires `confirm=True`) |
| `add_tool_to_agent` | Associate a tool with an agent, with input definitions |
| `remove_tool_from_agent` | Remove a tool from an agent |
| `create_agentic_workflow` | Create a new agentic workflow / use case |
| `update_agentic_workflow` | Update an existing workflow |
| `delete_agentic_workflow` | Delete a workflow (requires `confirm=True`) |
| `create_tool` | Create a new tool (flow action, script, search retrieval, etc.) |
| `update_tool` | Update an existing tool |
| `delete_tool` | Delete a tool (requires `confirm=True`) |
| `create_trigger` | Create a trigger for an agentic workflow |
| `update_trigger` | Update an existing trigger |
| `delete_trigger` | Delete a trigger (requires `confirm=True`) |

### 🛠️ Utility Tools

| Tool | Description |
|------|-------------|
| `clone_ai_agent` | Clone an agent with all its tools and configuration |
| `cleanup_agent_configs` | Remove duplicate `sn_aia_agent_config` records for an agent |

---

## Admin Bot — Instance Health Check

Automated diagnostic tool for ServiceNow demo instances. Runs 21 checks via REST API and generates an **interactive HTML report** with root cause analysis, fix steps, and copy-paste GlideRecord scripts — all in under 3 minutes.

> All checks are **read-only GET requests**. The tool makes no changes to your instance.

### The Problem It Solves

ServiceNow demo instances degrade silently over time:

```
Instance age: 0 days          Instance age: 60 days
──────────────────────        ──────────────────────────
Syslog:     400K records  →   Syslog:    45.7M records ❌
Errors:     0 / 5min      →   Errors:      340 / 5min  ❌
Toxic jobs: 0             →   Toxic jobs:           36 ❌
Benchmark:  350ms         →   Benchmark:       8,200ms ❌
```

The old fix: an experienced admin spending 1–2 hours running ad-hoc queries with no documentation. This tool automates the entire workflow in under 3 minutes.

### Why Python Instead of a Browser

Browsers enforce CORS — a security policy that blocks API calls to a different domain. When an HTML file loaded from `file://` tries to call `yourinstance.service-now.com`, the browser blocks it.

Python has no such restriction:

```
Browser (sn_admin_bot.html)        Python (healthcheck.py)
───────────────────────────        ───────────────────────
fetch → CORS blocked ❌            requests.get → response ✅
Needs CORS rule on instance        No configuration needed
file:// origin = broken            Works on any instance, any time
```

The `sn_admin_bot.html` browser version is included as a fallback for environments where Python is not available.

### Quick Start

```bash
cd admin_bot
cp .env.template .env
# Edit .env with your credentials

# Mac / Linux
bash run_healthcheck.sh

# Windows
run_healthcheck.bat

# Command line (pass credentials directly)
python3 healthcheck.py yourinstance.service-now.com admin yourpassword
```

An interactive HTML report opens in your browser automatically.

### How It Works

```
Step 1             Step 2              Step 3               Step 4
──────────         ────────────        ────────────         ──────────────────
bash               Python reads        25–30 GET            Interactive HTML
run_healthcheck    your .env file      requests to          report opens in
.sh                credentials         ServiceNow           your browser
                                       REST API
                                       (no browser,
                                       no CORS)
```

### The 21 Checks

**Phase 1 — Triage** *(2–3 minutes, nothing changed)*

| Check | Healthy | Problem |
|-------|---------|---------|
| Syslog table size | Under 5M records | Over 20M records |
| Errors in last 5 min | Under 20 | Over 100 |
| Toxic scheduled jobs | Zero | Any |

Based on these three numbers, the bot decides **Standard (Path 1)** or **Emergency (Path 2)**.

**Phase 2 — Database Tier (D1–D7)**

| # | Check | Warn | Fail |
|---|-------|------|------|
| D1 | Syslog size | >5M | >20M |
| D2 | Audit log (sys_audit) | >5M | >10M |
| D3 | Retention jobs configured | None found | — |
| D4 | Journal field records | >2M | >5M |
| D5 | Flow context records | >500K | >1M |
| D6 | Connection pool errors (1hr) | — | Any |
| D7 | Deadlocks (1hr) | — | Any |

**Phase 2 — Application Tier (A1–A4)**

| # | Check | Warn | Fail |
|---|-------|------|------|
| A1 | High-frequency jobs (<60s) | — | Any |
| A2 | Live error rate (5 min) | >20 | >100 |
| A3 | Flow Designer errors (1hr) | >1 | >10 |
| A4 | Semaphore utilization | >50% | >80% |

**Phase 3 — Transaction Tier Benchmark**

The bot runs each query **5 times** and calculates average + variance. Variance is often more informative than average — an instance with `350ms avg ±140ms variance` has background noise problems even if the average looks acceptable.

| Query | Why This One |
|-------|-------------|
| T1 — Syslog 7-day scan | Large table scan. Directly sensitive to syslog bloat. |
| T2 — P1/P2 Active Incidents | Small filtered query. Tests index and query engine health. |
| T3 — Flow Context 30d | Medium query. Shows automation overhead. |
| T4 — Active Users | ACL-heavy query. Tests security framework load. |

### Benchmark Grades

```
Total Score         Grade        What It Means
────────────────    ─────────    ─────────────────────────────────────────
Under 5,000ms    → EXCELLENT    Healthy. Ready for demos.
5,000–10,000ms   → GOOD         Minor issues. Won't impact demos.
10,000–20,000ms  → FAIR         Remediation recommended.
20,000–40,000ms  → POOR         Take action before using for demos.
Over 40,000ms    → CRITICAL     Do not use for demos until fixed.
```

### Interactive Report Features

When you click a non-healthy row in the report, it expands to show:

```
┌───────────────────────────────────────────────────────────────────┐
│  ● Service Mapping (CMDB)    ✗ Error                         ▼   │
├───────────────────────────────────────────────────────────────────┤
│  [ ROOT CAUSE ] [ FIX STEPS ] [ BACKGROUND SCRIPT ] [ OPEN ]    │
│                                                                   │
│  ROOT CAUSE                                                       │
│  The Service Mapping coordinator is referencing a cmdb_timeline   │
│  record that no longer exists. Typically caused by:              │
│  • A service deleted while recomputation was in progress          │
│  • A data cleanup overwriting CMDB state                          │
│                                                                   │
│  BACKGROUND SCRIPT                             📋 Copy           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ var gr = new GlideRecord('cmdb_timeline');                  │ │
│  │ gr.get('4682e9dc93f45650b5a87fba2bba1012');                 │ │
│  │ if (gr.isValid()) { gr.deleteRecord(); }                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  [ Open in Instance → ]  (deep-links to exact record/table)      │
└───────────────────────────────────────────────────────────────────┘
```

### Real Example: Live Session Results

*Run on `demoalectriallwfzu134583.service-now.com`, March 2026*

| Check | Result | Status |
|-------|--------|--------|
| Syslog records | 45.7M | ❌ FAIL |
| Errors (5 min) | 0 | ✅ OK |
| Toxic jobs | 0 | ✅ OK |
| **Decision** | **PATH 2 — EMERGENCY** | syslog bloat triggered emergency path |

| Query | Average | Variance |
|-------|---------|----------|
| T1 — Syslog 7-day scan | 101ms | ±37ms |
| T2 — P1/P2 Incidents | 103ms | ±12ms |
| T3 — Flow Context 30d | 109ms | ±53ms |
| T4 — Active Users | 101ms | ±12ms |
| **Total** | **413ms** | **EXCELLENT ✅** |

> Despite 45.7M syslog records, benchmark performance was EXCELLENT — showing that syslog bloat should be addressed proactively before it degrades over time.

### 6 Ways to Use the Admin Bot

**1. Demo Prep** — Run the night before any customer meeting.
```bash
bash admin_bot/run_healthcheck.sh
```
Grade GOOD or better = you're clear to go.

**2. T+48hr Benchmark** — Apply fixes, then confirm they held 48 hours later.
The variance drop is the key signal: `±140ms → ±19ms` means background noise is eliminated.

**3. Fleet-wide Check** — All your team's instances in one command:
```bash
#!/bin/bash
PASSWORD="shared_password"
INSTANCES=("instance1.service-now.com" "instance2.service-now.com")
for INSTANCE in "${INSTANCES[@]}"; do
  python3 admin_bot/healthcheck.py $INSTANCE admin $PASSWORD
done
```

**4. Scheduled Weekly Report** — Automatic, no manual work. Mac cron:
```bash
0 8 * * 1 cd ~/servicenow-mcp-server && bash admin_bot/run_healthcheck.sh
```

**5. SI Partner Enablement Workshop** — 60-minute hands-on lab. Every attendee runs the health check on their own instance and applies a fix live. Teaches MCP, REST APIs, CORS, and ServiceNow table architecture through direct experience.

**6. Customer Demo** — Run live in front of the customer. Real data. Real findings. Real fixes.
> *"This is not a pre-programmed dashboard. Claude read the actual error logs, understood what they mean, and categorized them by area and priority — in real time."*

### Admin Bot — Key Learnings for SI Partners

**Tool type is critical.** Only `script` type tools are reliably visible in AI Agent Studio UI. `record_operation` and `flow_action` types return HTTP 201 but are silently invisible in the tool tab. Always default to `script`.

**The variance number tells the real story.** An instance with `350ms ±10ms variance` is healthy. An instance with `350ms ±140ms variance` has background noise — even though the average looks the same. The variance drop is your confirmation that a fix actually worked.

**Most common issues on SC demo instances:**

| Issue | Why It Happens | Typical Fix |
|-------|----------------|-------------|
| Unconfigured agent policies firing | Demo instances cloned from templates include Azure/K8s monitoring configs but no agents connected | 5 min — bulk deactivate |
| DataCollector jobs stuck in loops | After cloning or upgrades, PA jobs lose their data baseline and loop trying to backfill months of missing history | 2 min — deactivate job |
| GRC/Security Center jobs running too often | Daily collection on large GRC datasets generates tens of thousands of SQL queries per run | 1 min — change to weekly |
| Business rules hitting missing fields | After upgrades or template cloning, business rules sometimes reference fields that no longer exist | 5 min — add null guard |
| Syslog over 5M with no cleanup job | Long-running instances accumulate logs forever without a retention policy | 10 min — create cleanup job |

---

## Key Learnings for SI Partners

These are hard-won lessons from building and debugging ServiceNow AI Agent implementations:

**Tool type is critical.** In ServiceNow AI Agent Studio, only `script` type tools are reliably visible in the UI. `record_operation` and `flow_action` types return HTTP 201 but are silently invisible — always default to `script`.

**Role scoping matters.** `sn_aia_admin` role is required to access AI agent configuration tables, not just standard admin.

**Destructive operations require two calls.** `delete_ai_agent`, `delete_agentic_workflow`, `delete_trigger`, `delete_tool` require calling first without `confirm=True` to see the warning, then with `confirm=True`.

**`add_tool_to_agent` convention.** Use `max_automatic_executions=3` for write tools, `5` for read tools.

**`cleanup_agent_configs`.** Run when an agent shows inconsistent active status between UI and API — targets duplicate `sn_aia_agent_config` records.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `401 Authentication failed` | Verify `SERVICENOW_USERNAME` and `SERVICENOW_PASSWORD` in `.env`. Confirm you can log in via browser. |
| `Connection timed out` | Check `SERVICENOW_INSTANCE` starts with `https://`. PDI instances hibernate — open in browser first to wake. |
| `403 on AI Agent tables` | Write operations require `sn_aia_admin` role — separate from standard admin. |
| `Tools not appearing in Claude Desktop (no 🔨 icon)` | Use absolute paths in config. Restart Claude Desktop after any change. Settings → Developer to check errors. |
| `ModuleNotFoundError` | Activate venv: `source venv/bin/activate` then `pip install -r requirements.txt`. |
| `CORS error (browser version of Admin Bot)` | Expected. Use `healthcheck.py` instead. |
| `Windows: script blocked by SmartScreen` | Right-click `run_healthcheck.bat` → Properties → Unblock. |
| `Mac: script blocked by Gatekeeper` | Right-click `run_healthcheck.sh` → Open → Open anyway. |
| `Report shows N/A for a check` | API returned 403 for that specific table. Other checks are still valid. |

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new tools, running tests, and submitting pull requests.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

## Disclaimer

This project is not affiliated with, endorsed by, or supported by ServiceNow, Inc. "ServiceNow" is a registered trademark of ServiceNow, Inc. Use of ServiceNow APIs is subject to your organization's ServiceNow license agreement.

---

*Built by Ihnaee Choi · AI Solution Architect, SI Partner Enablement*
*github.com/annie2000/servicenow-mcp-server · Apache 2.0 · v2.0 · March 2026*
