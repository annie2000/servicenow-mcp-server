# ServiceNow Admin Bot — Instance Health Check

Automated health check tool for ServiceNow demo instances.  
Runs 21 diagnostic checks via REST API. Generates a self-contained HTML report.  
No browser required during data collection — CORS does not apply.

---

## What It Checks

| Phase | Checks |
|---|---|
| **Triage** | Syslog size, live error rate, toxic scheduled jobs |
| **Database Tier (D1–D7)** | Syslog, audit log, retention jobs, journal fields, flow context, connection pool errors, deadlocks |
| **Application Tier (A1–A4)** | High-frequency jobs, live error rate, Flow Designer failures, semaphore utilization |
| **Benchmark (T1–T4)** | 5×4 timed queries — syslog, incidents, flow context, active users |

---

## Quick Start

### Step 1 — Set up credentials

Copy `.env.template` to `.env` and fill in your instance details:

```
SERVICENOW_INSTANCE=https://yourinstance.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your_password
```

### Step 2 — Run the health check

**Mac / Linux:**
```bash
bash run_healthcheck.sh
```

**Windows:**
```
Double-click run_healthcheck.bat
```

**Command line (any OS):**
```bash
python3 healthcheck.py yourinstance.service-now.com admin yourpassword
```

### Step 3 — Review the report

The script opens a timestamped HTML report in your browser automatically:
```
healthcheck_yourinstance_20260312_1430.html
```

---

## File Structure

| File | Purpose |
|---|---|
| `healthcheck.py` | Main script — all checks, benchmark, HTML report generator |
| `run_healthcheck.sh` | Mac/Linux launcher — double-click or `bash run_healthcheck.sh` |
| `run_healthcheck.bat` | Windows launcher — double-click to run |
| `sn_admin_bot.html` | Browser-based fallback — no Python required (CORS limitations apply) |
| `.env.template` | Credentials template — copy to `.env` and fill in your values |
| `README.md` | This file |

---

## Why Python Instead of a Browser

Browsers enforce CORS (Cross-Origin Resource Sharing) — a security policy that blocks API calls to a different domain. When you open `sn_admin_bot.html` from your desktop and it tries to call `yourinstance.service-now.com`, the browser blocks the request.

Python has no such restriction. It connects directly to the ServiceNow REST API and reads the response. The HTML report is then generated locally and opened in your browser as a static file — no new API calls are made at that point.

The `sn_admin_bot.html` browser version is included as a fallback for environments where Python is not available, but the Python version (`healthcheck.py`) is the recommended approach.

---

## Benchmark Grades

| Grade | Total Score | Meaning |
|---|---|---|
| EXCELLENT | Under 5,000ms | Healthy. No performance concerns. |
| GOOD | 5,000–10,000ms | Minor issues. Address at next opportunity. |
| FAIR | 10,000–20,000ms | Remediation recommended. |
| POOR | 20,000–40,000ms | Take action this session. |
| CRITICAL | Over 40,000ms | Do not use for demos until fixed. |

---

## Troubleshooting

| Error | Fix |
|---|---|
| `python3: command not found` | Install Python 3.8+ from python.org. On Mac: `brew install python3` |
| `ModuleNotFoundError: requests` | Run: `pip3 install requests` (launchers do this automatically) |
| HTTP 401 | Wrong username or password. Check your `.env` file. |
| HTTP 403 | User does not have read access to the table. Admin role required. |
| Connection refused / timeout | Instance may be hibernated. Open it in a browser first. |
| CORS error (browser version) | Expected. Use `healthcheck.py` instead. |
| Windows: script blocked | Right-click → Properties → Unblock |
| Mac: script blocked | Right-click → Open → Open anyway |

---

## Security

- All checks are **read-only GET requests** — the script makes no changes to your instance
- Credentials are stored only in your local `.env` file
- The generated HTML report contains aggregated counts only — no raw records, no credentials, no PII
- Never commit your `.env` file to version control

---

## Requirements

- Python 3.8 or higher
- `requests` library (installed automatically by the launcher scripts)
- ServiceNow admin credentials

---

*ServiceNow Admin Bot v1.0 · March 2026*  
*Ihnaee Choi · AI Solution Architect, SI Partner Enablement*  
*github.com/annie2000/servicenow-mcp-server · Apache 2.0*
