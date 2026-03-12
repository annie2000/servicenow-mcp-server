#!/usr/bin/env python3
"""
ServiceNow Admin Bot — Instance Health Check
v1.0 · March 2026
Ihnaee Choi · AI Solution Architect, SI Partner Enablement
github.com/annie2000/servicenow-mcp-server

Runs 21 diagnostic checks against a ServiceNow instance via REST API.
Generates a self-contained HTML report and opens it in your browser.
No browser is used during data collection — CORS does not apply.
"""

import sys
import os
import json
import time
import webbrowser
import tempfile
from datetime import datetime

# ── Dependency check ─────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("Installing required dependency: requests")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env loading is optional

# ── Credential loading (3 methods, tried in order) ───────────────────────────
def load_credentials():
    """
    Load credentials in priority order:
    1. Command-line arguments
    2. .env file (via environment variables)
    3. Interactive prompt
    """
    if len(sys.argv) == 4:
        instance = sys.argv[1].strip().rstrip("/")
        if not instance.startswith("http"):
            instance = "https://" + instance
        return instance, sys.argv[2], sys.argv[3]

    instance = os.getenv("SERVICENOW_INSTANCE", "").strip().rstrip("/")
    username = os.getenv("SERVICENOW_USERNAME", "").strip()
    password = os.getenv("SERVICENOW_PASSWORD", "").strip()

    if instance and username and password:
        return instance, username, password

    print("\nServiceNow Admin Bot — Instance Health Check")
    print("=" * 50)
    print("No credentials found in .env file or command-line arguments.")
    print("Enter credentials below (or Ctrl+C to cancel).\n")

    if not instance:
        raw = input("Instance URL (e.g. yourinstance.service-now.com): ").strip().rstrip("/")
        instance = "https://" + raw if not raw.startswith("http") else raw
    if not username:
        username = input("Username: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Password: ")

    return instance, username, password


# ── HTTP session ──────────────────────────────────────────────────────────────
SESSION = None

def init_session(username, password):
    global SESSION
    SESSION = requests.Session()
    SESSION.auth = (username, password)
    SESSION.headers.update({"Accept": "application/json"})
    SESSION.timeout = 20


def sn_count(table, query=""):
    """Return integer count of records matching query. Returns -1 on error."""
    try:
        params = {"sysparm_count": "true"}
        if query:
            params["sysparm_query"] = query
        r = SESSION.get(f"{INSTANCE}/api/now/stats/{table}", params=params)
        if r.status_code == 200:
            return int(r.json()["result"]["stats"]["count"])
        return -1
    except Exception:
        return -1


def sn_records(table, query="", fields="", limit=50):
    """Return list of records. Returns [] on error."""
    try:
        params = {"sysparm_limit": str(limit)}
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = fields
        r = SESSION.get(f"{INSTANCE}/api/now/table/{table}", params=params)
        if r.status_code == 200:
            return r.json().get("result", [])
        return []
    except Exception:
        return []


# ── Scoring helpers ───────────────────────────────────────────────────────────
def state(val, warn, fail):
    if val < 0:
        return "unknown"
    if val >= fail:
        return "fail"
    if val >= warn:
        return "warn"
    return "ok"


def fmt(n):
    if n < 0:
        return "N/A"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def grade_label(total_ms):
    if total_ms < 5000:
        return "EXCELLENT", "#16C553"
    if total_ms < 10000:
        return "GOOD", "#4dabf7"
    if total_ms < 20000:
        return "FAIR", "#FFB020"
    if total_ms < 40000:
        return "POOR", "#FF6B35"
    return "CRITICAL", "#FF3B5C"


# ── Main health check ─────────────────────────────────────────────────────────
def run_health_check():
    results = {}
    instance_name = INSTANCE.replace("https://", "").replace("http://", "")
    print(f"\n{'='*60}")
    print(f"  ServiceNow Admin Bot — Health Check")
    print(f"  Instance : {instance_name}")
    print(f"  Started  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # ── PHASE 1: TRIAGE ───────────────────────────────────────────────────────
    print("PHASE 1 — Quick Triage")
    print("-" * 40)

    print("  [T1] Syslog table size...", end=" ", flush=True)
    results["syslog_count"] = sn_count("syslog")
    print(fmt(results["syslog_count"]), "—", state(results["syslog_count"], 5_000_000, 20_000_000).upper())

    print("  [T2] Active errors (last 5 min)...", end=" ", flush=True)
    err_q = "level=error^sys_created_onRELATIVEGT@minute@ago@5"
    results["recent_errors"] = sn_count("syslog", err_q)
    print(fmt(results["recent_errors"]), "—", state(results["recent_errors"], 20, 100).upper())

    print("  [T3] Toxic scheduled jobs (<60s)...", end=" ", flush=True)
    toxic = sn_records("sysauto_script", "active=true^run_period<60", "name,run_period", 100)
    results["toxic_jobs"] = toxic
    results["toxic_count"] = len(toxic)
    st = "FAIL" if results["toxic_count"] > 0 else "OK"
    print(f"{results['toxic_count']} found — {st}")

    path = "PATH 2 — EMERGENCY" if (
        results["syslog_count"] > 20_000_000 or
        results["recent_errors"] > 100 or
        results["toxic_count"] > 0
    ) else "PATH 1 — STANDARD"
    results["path"] = path
    print(f"\n  Decision: {path}\n")

    # ── PHASE 2: DATABASE TIER ────────────────────────────────────────────────
    print("PHASE 2 — Full 21-Check Assessment")
    print("-" * 40)
    print("  Database Tier")

    print("  [D1] Syslog size...", end=" ", flush=True)
    results["d1"] = results["syslog_count"]
    print(fmt(results["d1"]), "—", state(results["d1"], 5_000_000, 20_000_000).upper())

    print("  [D2] Audit log (sys_audit)...", end=" ", flush=True)
    results["d2"] = sn_count("sys_audit")
    print(fmt(results["d2"]), "—", state(results["d2"], 5_000_000, 10_000_000).upper())

    print("  [D3] Retention jobs configured...", end=" ", flush=True)
    ret_q = "active=true^nameLIKEpurge^ORnameLIKEclean^ORnameLIKEretention"
    ret_jobs = sn_records("sysauto_script", ret_q, "name", 10)
    results["d3_jobs"] = [j.get("name", "") for j in ret_jobs]
    results["d3"] = len(ret_jobs)
    print(f"{results['d3']} found —", "OK" if results["d3"] > 0 else "WARN")

    print("  [D4] Journal field size...", end=" ", flush=True)
    results["d4"] = sn_count("sys_journal_field")
    print(fmt(results["d4"]), "—", state(results["d4"], 2_000_000, 5_000_000).upper())

    print("  [D5] Flow context records...", end=" ", flush=True)
    results["d5"] = sn_count("sys_flow_context")
    print(fmt(results["d5"]), "—", state(results["d5"], 500_000, 1_000_000).upper())

    print("  [D6] Connection pool errors (1hr)...", end=" ", flush=True)
    ce_q = "messageLIKEconnection pool^sys_created_onRELATIVEGT@hour@ago@1"
    results["d6"] = sn_count("syslog", ce_q)
    print(fmt(results["d6"]), "—", state(results["d6"], 1, 1).upper())

    print("  [D7] Deadlocks (1hr)...", end=" ", flush=True)
    dl_q = "messageLIKEdeadlock^sys_created_onRELATIVEGT@hour@ago@1"
    results["d7"] = sn_count("syslog", dl_q)
    print(fmt(results["d7"]), "—", state(results["d7"], 1, 1).upper())

    # ── PHASE 2: APPLICATION TIER ─────────────────────────────────────────────
    print("\n  Application Tier")

    print("  [A1] High-frequency jobs (<60s)...", end=" ", flush=True)
    hf = sn_records("sysauto_script", "active=true^run_period<60", "name,run_period", 50)
    results["a1_jobs"] = hf
    results["a1"] = len(hf)
    print(f"{results['a1']} found —", "FAIL" if results["a1"] > 0 else "OK")

    print("  [A2] Live error rate (5 min)...", end=" ", flush=True)
    results["a2"] = results["recent_errors"]
    print(fmt(results["a2"]), "—", state(results["a2"], 20, 100).upper())

    print("  [A3] Flow Designer errors (1hr)...", end=" ", flush=True)
    fe_q = "status=error^sys_created_onRELATIVEGT@hour@ago@1"
    results["a3"] = sn_count("sys_flow_context", fe_q)
    print(fmt(results["a3"]), "—", state(results["a3"], 1, 10).upper())

    print("  [A4] Semaphore utilization...", end=" ", flush=True)
    sem = sn_records("sys_semaphore", "", "waiting,sleeping,locked", 1)
    if sem:
        s = sem[0]
        waiting = int(s.get("waiting", 0) or 0)
        results["a4"] = waiting
        print(f"{waiting} waiting —", state(waiting, 50, 80).upper())
    else:
        results["a4"] = -1
        print("N/A")

    # ── PHASE 3: BENCHMARK ────────────────────────────────────────────────────
    print("\n  Transaction Tier — Benchmark (5 runs each)")

    bench_tests = [
        ("t1", "T1 — Syslog 7-day scan",     "syslog",           "sys_created_onRELATIVEGT@day@ago@7"),
        ("t2", "T2 — P1/P2 Active Incidents", "incident",         "active=true^priority<=2"),
        ("t3", "T3 — Flow Context 30d",        "sys_flow_context", "sys_created_onRELATIVEGT@day@ago@30"),
        ("t4", "T4 — Active Users",            "sys_user",         "active=true"),
    ]

    bench_results = {}
    total_ms = 0

    for key, label, table, query in bench_tests:
        print(f"  [{key.upper()}] {label}...", end=" ", flush=True)
        times = []
        for _ in range(5):
            t0 = time.time()
            sn_count(table, query)
            times.append((time.time() - t0) * 1000)
        avg = sum(times) / len(times)
        variance = max(times) - min(times)
        bench_results[key] = {"avg": round(avg), "variance": round(variance), "times": [round(t) for t in times]}
        total_ms += avg
        print(f"{round(avg)}ms avg  ±{round(variance)}ms variance")

    total_ms = round(total_ms)
    grade, grade_color = grade_label(total_ms)
    results["bench"] = bench_results
    results["bench_total"] = total_ms
    results["grade"] = grade
    results["grade_color"] = grade_color

    print(f"\n  Total Score : {total_ms}ms — {grade}")

    # ── FIX RECOMMENDATIONS ───────────────────────────────────────────────────
    fixes = []

    if results["syslog_count"] > 20_000_000:
        fixes.append({
            "priority": "P1",
            "title": "Syslog table exceeds 20M records",
            "description": "Syslog bloat is the #1 cause of slow instances. Create a retention job to purge records older than 30 days.",
            "script": """// Create Syslog Cleanup Job
// Navigate to: System Definition > Scheduled Jobs > New
// Name: Syslog Cleanup - 30 Day Retention
// Run: Daily
// Script:
var gr = new GlideRecord('syslog');
gr.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');
gr.deleteMultiple();
gs.info('Syslog cleanup complete');"""
        })

    if results["toxic_count"] > 0:
        job_names = ", ".join(j.get("name", "unknown") for j in results["toxic_jobs"][:5])
        fixes.append({
            "priority": "P1",
            "title": f"Toxic scheduled jobs detected: {results['toxic_count']} jobs running faster than every 60 seconds",
            "description": f"Jobs running sub-60s intervals hammer the database. Affected jobs: {job_names}",
            "script": """// Navigate to: System Definition > Scheduled Jobs
// Find each job listed above
// Change Run Period to at least 300 seconds (5 minutes)
// Or deactivate if the job is not needed"""
        })

    if results["recent_errors"] > 100:
        fixes.append({
            "priority": "P1",
            "title": f"High error rate: {fmt(results['recent_errors'])} errors in the last 5 minutes",
            "description": "Active error flood detected. Check syslog for the error source and address the root cause.",
            "script": """// Query syslog to identify error sources:
// Navigate to: System Logs > System Log > All
// Filter: Level = Error, Created > 5 minutes ago
// Sort by Source to identify the highest-frequency error"""
        })

    if results["d2"] > 10_000_000:
        fixes.append({
            "priority": "P2",
            "title": f"Audit log at {fmt(results['d2'])} records",
            "description": "sys_audit table is large. Review audit policy and purge old records.",
            "script": """// Create Audit Log Cleanup Job
var gr = new GlideRecord('sys_audit');
gr.addEncodedQuery('sys_created_onRELATIVELT@day@ago@90');
gr.deleteMultiple();
gs.info('Audit log cleanup complete');"""
        })

    if results["d5"] > 1_000_000:
        fixes.append({
            "priority": "P2",
            "title": f"Flow context table at {fmt(results['d5'])} records",
            "description": "Old flow execution records accumulate. Purge records older than 30 days.",
            "script": """// Create Flow Context Cleanup Job
var gr = new GlideRecord('sys_flow_context');
gr.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');
gr.deleteMultiple();
gs.info('Flow context cleanup complete');"""
        })

    if results["d3"] == 0:
        fixes.append({
            "priority": "P3",
            "title": "No retention jobs configured",
            "description": "Without retention jobs, tables grow indefinitely. Create cleanup jobs for syslog, sys_audit, and sys_flow_context.",
            "script": """// See P1/P2 fix scripts above for cleanup job templates
// Recommended retention periods:
//   syslog          → 30 days
//   sys_audit       → 90 days
//   sys_flow_context → 30 days
//   sys_journal_field → 180 days"""
        })

    results["fixes"] = fixes

    print(f"\n  {len(fixes)} fix recommendation(s) generated")
    print(f"\n{'='*60}")
    print(f"  Health check complete.")
    print(f"{'='*60}\n")

    return results


# ── HTML Report Generation ────────────────────────────────────────────────────
def build_html_report(results, instance_name, run_time):
    grade      = results.get("grade", "UNKNOWN")
    grade_color = results.get("grade_color", "#888")
    total_ms   = results.get("bench_total", 0)
    fixes      = results.get("fixes", [])
    bench      = results.get("bench", {})
    path       = results.get("path", "")

    inst_url   = ("https://" + instance_name) if not instance_name.startswith("http") else instance_name

    # ── Status helpers ────────────────────────────────────────────────────────
    def badge(st):
        return {
            "ok":      '<span class="badge healthy">✓ Healthy</span>',
            "warn":    '<span class="badge warning">⚠ Warning</span>',
            "fail":    '<span class="badge error">✕ Error</span>',
            "unknown": '<span class="badge idle">? Unknown</span>',
        }.get(st, '<span class="badge idle">? Unknown</span>')

    def sev_class(st):
        return {"ok": "", "warn": "sev-warning", "fail": "sev-error", "unknown": "sev-check"}.get(st, "sev-check")

    def is_unhealthy(st):
        return st in ("warn", "fail", "unknown")

    # ── Per-check definitions ─────────────────────────────────────────────────
    d1_st = state(results["d1"], 5_000_000, 20_000_000)
    d2_st = state(results["d2"], 5_000_000, 10_000_000)
    d3_st = "ok" if results["d3"] > 0 else "warn"
    d4_st = state(results["d4"], 2_000_000, 5_000_000)
    d5_st = state(results["d5"], 500_000, 1_000_000)
    d6_st = state(results["d6"], 1, 1)
    d7_st = state(results["d7"], 1, 1)
    a1_st = "fail" if results["a1"] > 0 else "ok"
    a2_st = state(results["a2"], 20, 100)
    a3_st = state(results["a3"], 1, 10)
    a4_st = state(results["a4"], 50, 80) if results["a4"] >= 0 else "unknown"

    toxic_names = ", ".join(j.get("name", "?") for j in results.get("toxic_jobs", [])[:5]) or "N/A"
    a1_job_rows = "".join(
        f'<li style="margin-bottom:4px;color:var(--text2)"><code>{j.get("name","?")}</code> — {j.get("run_period","?")}s interval</li>'
        for j in results.get("a1_jobs", [])[:20]
    )

    checks = [
        # ── Database Tier ────────────────────────────────────────────────────
        {
            "id": "d1", "group": "Database Tier",
            "label": "D1 — Syslog Size",
            "value": fmt(results["d1"]),
            "status": d1_st,
            "notes": f"{fmt(results['d1'])} records · Warn &gt;5M · Fail &gt;20M",
            "cause": "The <code>syslog</code> table stores every platform event. Without retention it grows unbounded, causing full-table scans on every read. Above 20M records query performance degrades severely and node restarts slow down.",
            "steps": [
                "Navigate to <strong>System Definition &gt; Scheduled Jobs</strong> and create a new <em>Automatically run script</em> job.",
                "Name it <em>Syslog Cleanup — 30 Day Retention</em>, set to run <strong>Daily</strong>.",
                "Paste the cleanup script from the next tab.",
                "Save, then right-click the job &gt; <strong>Execute Now</strong> to run immediately.",
                "Monitor daily until the count stabilises below 5M records.",
            ],
            "script": "// Syslog Cleanup — 30 Day Retention\n// Run in: {url}/sys.scripts.do\n\n// Step 1: Count records that will be purged\nvar count = new GlideRecord('syslog');\ncount.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');\ncount.query();\ngs.info('Records to purge: ' + count.getRowCount());\n\n// Step 2: Purge (uncomment after confirming count above)\n/*\nvar gr = new GlideRecord('syslog');\ngr.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');\ngr.deleteMultiple();\ngs.info('Syslog cleanup complete');\n*/".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Syslog Table", "url": inst_url + "/syslog_list.do", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "⏱ Scheduled Jobs", "url": inst_url + "/sysauto_script_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "d2", "group": "Database Tier",
            "label": "D2 — Audit Log (sys_audit)",
            "value": fmt(results["d2"]),
            "status": d2_st,
            "notes": f"{fmt(results['d2'])} records · Warn &gt;5M · Fail &gt;10M",
            "cause": "The <code>sys_audit</code> table tracks every field-level change for audited records. Without a retention policy it grows continuously. Large audit tables slow down record saves (every write triggers audit inserts) and inflate storage.",
            "steps": [
                "Confirm which tables have auditing enabled: <strong>System Definition &gt; Dictionary</strong>, filter <em>Audit = true</em>.",
                "Disable auditing on non-critical tables if appropriate.",
                "Create a Scheduled Job to purge audit records older than 90 days using the script in the next tab.",
                "Consider adjusting the retention window based on your compliance requirements.",
            ],
            "script": "// Audit Log Cleanup — 90 Day Retention\n// Run in: {url}/sys.scripts.do\n\n// Step 1: Count records to purge\nvar count = new GlideRecord('sys_audit');\ncount.addEncodedQuery('sys_created_onRELATIVELT@day@ago@90');\ncount.query();\ngs.info('Audit records to purge: ' + count.getRowCount());\n\n// Step 2: Purge (uncomment after confirming count)\n/*\nvar gr = new GlideRecord('sys_audit');\ngr.addEncodedQuery('sys_created_onRELATIVELT@day@ago@90');\ngr.deleteMultiple();\ngs.info('Audit log cleanup complete');\n*/".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Audit Log Table", "url": inst_url + "/sys_audit_list.do", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "⏱ Scheduled Jobs", "url": inst_url + "/sysauto_script_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "d3", "group": "Database Tier",
            "label": "D3 — Retention Jobs",
            "value": f"{results['d3']} configured",
            "status": d3_st,
            "notes": "No active cleanup/purge/retention scheduled jobs found" if d3_st == "warn" else f"{results['d3']} retention job(s) active",
            "cause": "No active scheduled jobs with names containing <em>purge</em>, <em>clean</em>, or <em>retention</em> were found. Without retention jobs, all major tables (syslog, sys_audit, sys_flow_context, sys_journal_field) grow indefinitely, leading to performance degradation over time.",
            "steps": [
                "Go to <strong>System Definition &gt; Scheduled Jobs</strong>.",
                "Create retention jobs for at minimum: <code>syslog</code> (30 days), <code>sys_audit</code> (90 days), <code>sys_flow_context</code> (30 days), <code>sys_journal_field</code> (180 days).",
                "Use type <strong>Automatically run script</strong> with a <strong>Daily</strong> schedule.",
                "Use the script template in the next tab as a starting point for each table.",
            ],
            "script": "// Retention Job Templates\n// Run in: {url}/sys.scripts.do\n// Create one Scheduled Job per table\n\n// === syslog (30 days) ===\nvar g1 = new GlideRecord('syslog');\ng1.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');\ng1.deleteMultiple();\ngs.info('syslog cleanup done');\n\n// === sys_audit (90 days) ===\n// var g2 = new GlideRecord('sys_audit');\n// g2.addEncodedQuery('sys_created_onRELATIVELT@day@ago@90');\n// g2.deleteMultiple();\n// gs.info('sys_audit cleanup done');\n\n// === sys_flow_context (30 days) ===\n// var g3 = new GlideRecord('sys_flow_context');\n// g3.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');\n// g3.deleteMultiple();\n// gs.info('sys_flow_context cleanup done');".replace("{url}", inst_url),
            "links": [
                {"label": "⏱ Scheduled Jobs", "url": inst_url + "/sysauto_script_list.do", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
            ],
        },
        {
            "id": "d4", "group": "Database Tier",
            "label": "D4 — Journal Field Records",
            "value": fmt(results["d4"]),
            "status": d4_st,
            "notes": f"{fmt(results['d4'])} records · Warn &gt;2M · Fail &gt;5M",
            "cause": "<code>sys_journal_field</code> stores work notes and comments for every record. It accumulates rapidly on active instances — each comment or work note creates a new row. Large journal tables slow down record form loads and related list queries.",
            "steps": [
                "Determine which tables generate the most journal activity: query <code>sys_journal_field</code> grouped by <code>element_id</code> table prefix.",
                "Create a retention job to purge journal entries older than 180 days for closed/resolved records.",
                "Alternatively, use ServiceNow's built-in <strong>Data Archiving</strong> feature for journal data.",
            ],
            "script": "// Journal Field Cleanup — 180 Day Retention\n// Run in: {url}/sys.scripts.do\n\n// Step 1: Count records to purge\nvar count = new GlideRecord('sys_journal_field');\ncount.addEncodedQuery('sys_created_onRELATIVELT@day@ago@180');\ncount.query();\ngs.info('Journal records to purge: ' + count.getRowCount());\n\n// Step 2: Top tables by journal volume\nvar topTables = {};\nvar scan = new GlideRecord('sys_journal_field');\nscan.setLimit(10000);\nscan.query();\nwhile (scan.next()) {\n  var t = scan.getValue('name') || 'unknown';\n  topTables[t] = (topTables[t] || 0) + 1;\n}\ngs.info('Journal breakdown: ' + JSON.stringify(topTables));".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Journal Field Table", "url": inst_url + "/sys_journal_field_list.do", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "⏱ Scheduled Jobs", "url": inst_url + "/sysauto_script_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "d5", "group": "Database Tier",
            "label": "D5 — Flow Context Records",
            "value": fmt(results["d5"]),
            "status": d5_st,
            "notes": f"{fmt(results['d5'])} records · Warn &gt;500K · Fail &gt;1M",
            "cause": "<code>sys_flow_context</code> stores a record for every Flow Designer execution. Without cleanup, completed flow contexts accumulate indefinitely. Above 1M records, Flow Designer's execution history queries become slow, and the table bloats storage.",
            "steps": [
                "Navigate to <strong>Flow Designer &gt; Executions</strong> to confirm the oldest records still present.",
                "Create a Scheduled Job to purge flow contexts older than 30 days.",
                "Consider reducing the retention period to 14 days on high-volume instances.",
            ],
            "script": "// Flow Context Cleanup — 30 Day Retention\n// Run in: {url}/sys.scripts.do\n\n// Step 1: Count records to purge\nvar count = new GlideRecord('sys_flow_context');\ncount.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');\ncount.query();\ngs.info('Flow contexts to purge: ' + count.getRowCount());\n\n// Step 2: Purge (uncomment after confirming count)\n/*\nvar gr = new GlideRecord('sys_flow_context');\ngr.addEncodedQuery('sys_created_onRELATIVELT@day@ago@30');\ngr.deleteMultiple();\ngs.info('Flow context cleanup complete');\n*/".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Flow Executions", "url": inst_url + "/sys_flow_context_list.do", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "⏱ Scheduled Jobs", "url": inst_url + "/sysauto_script_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "d6", "group": "Database Tier",
            "label": "D6 — Connection Pool Errors (1hr)",
            "value": fmt(results["d6"]),
            "status": d6_st,
            "notes": f"{fmt(results['d6'])} errors in last hour · Fail: any",
            "cause": "Connection pool errors indicate the instance is exhausting its database connection limit. This happens when long-running transactions or high concurrency exceeds the pool size. Symptoms: slow UI, script timeouts, and cascading errors across all transactions.",
            "steps": [
                "Check syslog filtered to <em>connection pool</em> to identify the error frequency and source.",
                "Look for long-running transactions in <strong>System Diagnostics &gt; Session Debug</strong>.",
                "Review any recent deployments or scheduled jobs that may have introduced long-running queries.",
                "As a short-term fix, restart worker nodes if the issue is acute.",
                "Long term: optimize queries identified in the syslog and consider adding connection pool capacity.",
            ],
            "script": "// Connection Pool Error Analysis\n// Run in: {url}/sys.scripts.do\n\nvar gr = new GlideRecord('syslog');\ngr.addEncodedQuery('messageLIKEconnection pool^sys_created_onRELATIVEGT@hour@ago@1');\ngr.orderByDesc('sys_created_on');\ngr.setLimit(20);\ngr.query();\ngs.info('Connection pool errors (1hr): ' + gr.getRowCount());\nwhile (gr.next()) {\n  gs.info('[' + gr.getValue('sys_created_on') + '] ' + gr.getValue('message').substring(0, 200));\n}".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Connection Pool Errors", "url": inst_url + "/syslog_list.do?sysparm_query=messageLIKEconnection+pool", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "🔬 Session Debug", "url": inst_url + "/sys_session_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "d7", "group": "Database Tier",
            "label": "D7 — Deadlocks (1hr)",
            "value": fmt(results["d7"]),
            "status": d7_st,
            "notes": f"{fmt(results['d7'])} deadlocks in last hour · Fail: any",
            "cause": "Database deadlocks occur when two or more transactions hold locks that the other needs, and neither can proceed. In ServiceNow this usually manifests in business rules, workflows, or integrations that update the same records concurrently. Deadlocks cause transaction rollbacks and can cascade into user-visible errors.",
            "steps": [
                "Filter the syslog for <em>deadlock</em> to identify the tables and scripts involved.",
                "Look for business rules or integrations that update the same table simultaneously.",
                "Add explicit ordering or use <code>setWorkflow(false)</code> where appropriate to reduce lock contention.",
                "Consider converting synchronous business rules to async where ordering isn't critical.",
            ],
            "script": "// Deadlock Analysis\n// Run in: {url}/sys.scripts.do\n\nvar gr = new GlideRecord('syslog');\ngr.addEncodedQuery('messageLIKEdeadlock^sys_created_onRELATIVEGT@hour@ago@1');\ngr.orderByDesc('sys_created_on');\ngr.setLimit(20);\ngr.query();\ngs.info('Deadlocks in last hour: ' + gr.getRowCount());\nwhile (gr.next()) {\n  gs.info('[' + gr.getValue('sys_created_on') + '] Source: ' + gr.getValue('source'));\n  gs.info('  ' + gr.getValue('message').substring(0, 300));\n}".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Deadlock Entries", "url": inst_url + "/syslog_list.do?sysparm_query=messageLIKEdeadlock", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
            ],
        },
        # ── Application Tier ─────────────────────────────────────────────────
        {
            "id": "a1", "group": "Application Tier",
            "label": "A1 — High-Frequency Scheduled Jobs",
            "value": f"{results['a1']} found",
            "status": a1_st,
            "notes": f"{results['a1']} job(s) running faster than every 60 seconds" if a1_st == "fail" else "No sub-60s jobs found",
            "cause": f"Scheduled jobs running sub-60-second intervals hammer the database with repeated queries, often doing little useful work. Each execution opens a transaction, locks rows, and writes to syslog. The jobs detected are: <strong>{toxic_names}</strong>.",
            "steps": [
                "Go to <strong>System Definition &gt; Scheduled Jobs</strong> and locate each job listed above.",
                "Increase the <strong>Run Period</strong> to at least 300 seconds (5 minutes) — most jobs don't need sub-minute frequency.",
                "If a job must run frequently, audit its script to ensure it exits early when there is nothing to do.",
                "Deactivate any jobs that are no longer needed.",
            ],
            "script": ("// High-Frequency Job Analysis\n// Run in: {url}/sys.scripts.do\n\nvar gr = new GlideRecord('sysauto_script');\ngr.addQuery('active', 'true');\ngr.addQuery('run_period', '<', '60');\ngr.orderBy('run_period');\ngr.query();\ngs.info('Sub-60s jobs found: ' + gr.getRowCount());\nwhile (gr.next()) {\n  gs.info('  Job: ' + gr.getValue('name') + ' | Period: ' + gr.getValue('run_period') + 's');\n}\n\n// To bulk-update intervals to 300s (uncomment with care):\n/*\nvar fix = new GlideRecord('sysauto_script');\nfix.addQuery('active', 'true');\nfix.addQuery('run_period', '<', '60');\nfix.query();\nwhile (fix.next()) {\n  gs.info('Updating: ' + fix.getValue('name'));\n  fix.setValue('run_period', '300');\n  fix.update();\n}\n*/").replace("{url}", inst_url),
            "links": [
                {"label": "⏱ Scheduled Jobs (sub-60s)", "url": inst_url + "/sysauto_script_list.do?sysparm_query=active=true^run_period<60", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "⏱ All Scheduled Jobs", "url": inst_url + "/sysauto_script_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "a2", "group": "Application Tier",
            "label": "A2 — Live Error Rate (5 min)",
            "value": fmt(results["a2"]),
            "status": a2_st,
            "notes": f"{fmt(results['a2'])} errors in last 5 min · Warn &gt;20 · Fail &gt;100",
            "cause": "A high live error rate indicates an active failure on the instance — a recently deployed script, a broken integration, or a cascading failure from a resource issue. Above 100 errors/5min the instance is in an active incident state and requires immediate triage.",
            "steps": [
                "Open the syslog filtered to <em>level = error</em> and <em>created &gt; 5 minutes ago</em>.",
                "Sort by <strong>Source</strong> to identify the highest-frequency error source.",
                "Check for any recent deployments (Update Sets applied in the last hour).",
                "If a specific script is flooding errors, deactivate the business rule or scheduled job to stop the bleed.",
                "Open the Scripts — Background link and run the diagnostic script to group errors by source.",
            ],
            "script": "// Live Error Rate Analysis\n// Run in: {url}/sys.scripts.do\n\nvar sources = {};\nvar gr = new GlideRecord('syslog');\ngr.addQuery('level', 'error');\ngr.addEncodedQuery('sys_created_onRELATIVEGT@minute@ago@5');\ngr.query();\nwhile (gr.next()) {\n  var src = gr.getValue('source') || 'unknown';\n  sources[src] = (sources[src] || 0) + 1;\n}\n\n// Sort by frequency\nvar sorted = Object.entries(sources).sort((a,b) => b[1]-a[1]);\ngs.info('Top error sources (last 5 min):');\nsorted.slice(0,10).forEach(function(e) {\n  gs.info('  ' + e[0] + ': ' + e[1] + ' errors');\n});".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Recent Errors", "url": inst_url + "/syslog_list.do?sysparm_query=level=error^sys_created_onRELATIVEGT@minute@ago@5", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "📋 All Syslog", "url": inst_url + "/syslog_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "a3", "group": "Application Tier",
            "label": "A3 — Flow Designer Errors (1hr)",
            "value": fmt(results["a3"]),
            "status": a3_st,
            "notes": f"{fmt(results['a3'])} failed flow execution(s) · Warn &gt;1 · Fail &gt;10",
            "cause": "Flow Designer execution contexts with <em>error</em> status indicate flows that crashed at runtime. This can block automated processes, SLA timers, and integrations that depend on successful flow completion. Each error represents a process that did not complete.",
            "steps": [
                "Navigate to <strong>Flow Designer &gt; Executions</strong> and filter by Status = Error.",
                "Open each failed execution and review the <strong>Execution Log</strong> tab for the specific error.",
                "Common causes: script action failures, missing referenced records, permission errors, or API timeouts.",
                "Fix the underlying flow or script and re-trigger if the trigger condition still applies.",
            ],
            "script": "// Flow Designer Error Analysis\n// Run in: {url}/sys.scripts.do\n\nvar gr = new GlideRecord('sys_flow_context');\ngr.addQuery('status', 'error');\ngr.addEncodedQuery('sys_created_onRELATIVEGT@hour@ago@1');\ngr.orderByDesc('sys_created_on');\ngr.setLimit(20);\ngr.query();\ngs.info('Failed flows (1hr): ' + gr.getRowCount());\nwhile (gr.next()) {\n  gs.info('  Flow: ' + gr.getValue('name')\n    + ' | Started: ' + gr.getValue('start_time')\n    + ' | ID: ' + gr.getUniqueValue());\n}".replace("{url}", inst_url),
            "links": [
                {"label": "📋 Failed Flow Executions", "url": inst_url + "/sys_flow_context_list.do?sysparm_query=status=error^sys_created_onRELATIVEGT@hour@ago@1", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "📋 All Flow Executions", "url": inst_url + "/sys_flow_context_list.do", "style": "tertiary"},
            ],
        },
        {
            "id": "a4", "group": "Application Tier",
            "label": "A4 — Semaphore Utilization",
            "value": fmt(results["a4"]) if results["a4"] >= 0 else "N/A",
            "status": a4_st,
            "notes": f"{fmt(results['a4'])} thread(s) waiting · Warn &gt;50 · Fail &gt;80" if results["a4"] >= 0 else "Semaphore data unavailable",
            "cause": "High semaphore wait counts indicate thread contention — more requests are arriving than the instance can process concurrently. This causes UI slowness, transaction timeouts, and queued requests. It typically stems from long-running transactions or a surge in concurrent users.",
            "steps": [
                "Navigate to <strong>System Diagnostics &gt; Semaphore</strong> for a live view.",
                "Identify which transactions are holding semaphores the longest.",
                "Check for runaway scheduled jobs or business rules that don't exit quickly.",
                "Review node count — if consistently at capacity, consider adding a node.",
                "Use <strong>System Diagnostics &gt; Stats</strong> to review current thread pool utilization.",
            ],
            "script": "// Semaphore Utilization Analysis\n// Run in: {url}/sys.scripts.do\n\nvar sem = new GlideRecord('sys_semaphore');\nsem.query();\nif (sem.next()) {\n  gs.info('Semaphore status:');\n  gs.info('  Waiting : ' + sem.getValue('waiting'));\n  gs.info('  Sleeping: ' + sem.getValue('sleeping'));\n  gs.info('  Locked  : ' + sem.getValue('locked'));\n}\n\n// List long-running transactions\nvar tx = new GlideRecord('sys_running_transaction');\ntx.orderByDesc('elapsed_time');\ntx.setLimit(10);\ntx.query();\ngs.info('Top running transactions:');\nwhile (tx.next()) {\n  gs.info('  ' + tx.getValue('url') + ' | ' + tx.getValue('elapsed_time') + 'ms');\n}".replace("{url}", inst_url),
            "links": [
                {"label": "📊 Semaphore Monitor", "url": inst_url + "/sys_semaphore_list.do", "style": "primary"},
                {"label": "📊 Running Transactions", "url": inst_url + "/sys_running_transaction_list.do", "style": "primary"},
                {"label": "⚡ Scripts — Background", "url": inst_url + "/sys.scripts.do", "style": "secondary"},
                {"label": "📊 Stats", "url": inst_url + "/stats.do", "style": "tertiary"},
            ],
        },
    ]

    # ── HTML builders ─────────────────────────────────────────────────────────
    def render_links(links):
        parts = []
        for lnk in links:
            parts.append(
                f'<a class="inst-link {lnk["style"]}" href="{lnk["url"]}" target="_blank">{lnk["label"]}</a>'
            )
        return '<div class="links-row">' + "".join(parts) + "</div>"

    def render_steps(steps):
        items = "".join(f"<li>{s}</li>" for s in steps)
        return f'<ol class="steps">{items}</ol>'

    def render_expand(chk):
        cid   = chk["id"]
        sev   = sev_class(chk["status"])
        script_escaped = chk["script"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""
        <div class="expand-panel">
          <div class="expand-inner">
            <div style="display:flex">
              <div class="sev-bar {sev}"></div>
              <div style="flex:1">
                <div class="etabs">
                  <div class="etab active" onclick="switchTab(event,'{cid}','cause')">Root Cause</div>
                  <div class="etab" onclick="switchTab(event,'{cid}','fix')">Fix Steps</div>
                  <div class="etab" onclick="switchTab(event,'{cid}','script')">Background Script</div>
                  <div class="etab" onclick="switchTab(event,'{cid}','links')">Open in Instance</div>
                </div>
                <div id="{cid}-cause" class="epanel active">
                  <div class="elabel">Root Cause</div>
                  <div class="edesc">{chk["cause"]}</div>
                </div>
                <div id="{cid}-fix" class="epanel">
                  <div class="elabel">Step-by-Step Fix</div>
                  {render_steps(chk["steps"])}
                </div>
                <div id="{cid}-script" class="epanel">
                  <div class="elabel">Scripts — Background (sys.scripts.do)</div>
                  <div class="script-label-row">
                    <div class="edesc" style="font-size:13px">Copy and paste directly into <code>sys.scripts.do</code>:</div>
                    <div class="copy-btn" onclick="copyScript('{cid}-code')">&#128203; Copy</div>
                  </div>
                  <pre class="script" id="{cid}-code">{script_escaped}</pre>
                </div>
                <div id="{cid}-links" class="epanel">
                  <div class="elabel">Open in Instance</div>
                  {render_links(chk["links"])}
                </div>
              </div>
            </div>
          </div>
        </div>"""

    def render_row(chk):
        cid        = chk["id"]
        unhealthy  = is_unhealthy(chk["status"])
        clickable  = " clickable" if unhealthy else ""
        onclick    = f' onclick="toggleRow(\'{cid}\')"' if unhealthy else ""
        chevron    = '<span class="row-chevron">&#9662;</span>' if unhealthy else ""
        expand     = render_expand(chk) if unhealthy else ""
        row_class  = f' expandable-row" id="{cid}' if unhealthy else ""
        return f"""
        <tr class="row-summary{row_class}">
          <td colspan="4">
            <div class="row-inner{clickable}"{onclick}>
              <div class="row-area">{chk["label"]}</div>
              <div class="row-status">{badge(chk["status"])}</div>
              <div class="row-notes">{chk["notes"]}</div>
              <div class="row-action">{chevron}</div>
            </div>
            {expand}
          </td>
        </tr>"""

    # Group rows by section
    db_rows  = "".join(render_row(c) for c in checks if c["group"] == "Database Tier")
    app_rows = "".join(render_row(c) for c in checks if c["group"] == "Application Tier")

    # Benchmark rows
    bench_labels = {"t1": "T1 — Syslog 7-day scan", "t2": "T2 — P1/P2 Active Incidents",
                    "t3": "T3 — Flow Context 30d",   "t4": "T4 — Active Users"}
    bench_rows_html = ""
    for key in ["t1", "t2", "t3", "t4"]:
        b = bench.get(key, {})
        if b:
            avg = b.get("avg", 0)
            var = b.get("variance", 0)
            color = "var(--green)" if avg < 3000 else "var(--orange)" if avg < 8000 else "var(--red)"
            bench_rows_html += f"""
            <tr>
              <td style="padding:13px 16px;font-size:14px;color:var(--text2);border-bottom:1px solid rgba(46,50,72,0.5);">{bench_labels.get(key, key)}</td>
              <td style="padding:13px 16px;font-size:14px;text-align:right;font-weight:600;border-bottom:1px solid rgba(46,50,72,0.5);color:{color};">{avg}ms</td>
              <td style="padding:13px 16px;font-size:14px;text-align:right;border-bottom:1px solid rgba(46,50,72,0.5);color:var(--grey);">±{var}ms</td>
            </tr>"""

    # Fix recommendation cards (expandable)
    p_sev = {"P1": "fail", "P2": "warn", "P3": "warn"}
    p_label = {"P1": "High", "P2": "Medium", "P3": "Low"}
    fix_cards_html = ""
    for i, fix in enumerate(fixes):
        fid   = f"fix{i}"
        sev   = p_sev.get(fix["priority"], "warn")
        sev_c = sev_class(sev)
        script_esc = fix.get("script","").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        fix_cards_html += f"""
        <tr class="row-summary expandable-row" id="{fid}">
          <td colspan="4">
            <div class="row-inner clickable" onclick="toggleRow('{fid}')">
              <div class="row-area">{fix["title"]}</div>
              <div class="row-status"><span class="badge {'error' if sev=='fail' else 'warning'}">{p_label.get(fix['priority'], fix['priority'])}</span></div>
              <div class="row-notes">{fix["description"]}</div>
              <div class="row-action"><span class="row-chevron">&#9662;</span></div>
            </div>
            <div class="expand-panel">
              <div class="expand-inner">
                <div style="display:flex">
                  <div class="sev-bar {sev_c}"></div>
                  <div style="flex:1">
                    <div class="etabs">
                      <div class="etab active" onclick="switchTab(event,'{fid}','desc')">Description</div>
                      <div class="etab" onclick="switchTab(event,'{fid}','script')">Remediation Script</div>
                      <div class="etab" onclick="switchTab(event,'{fid}','links')">Open in Instance</div>
                    </div>
                    <div id="{fid}-desc" class="epanel active">
                      <div class="elabel">Details</div>
                      <div class="edesc">{fix["description"]}</div>
                    </div>
                    <div id="{fid}-script" class="epanel">
                      <div class="elabel">Remediation Script</div>
                      <div class="script-label-row">
                        <div class="edesc" style="font-size:13px">Copy and paste into <code>sys.scripts.do</code>:</div>
                        <div class="copy-btn" onclick="copyScript('{fid}-code')">&#128203; Copy</div>
                      </div>
                      <pre class="script" id="{fid}-code">{script_esc}</pre>
                    </div>
                    <div id="{fid}-links" class="epanel">
                      <div class="elabel">Open in Instance</div>
                      <div class="links-row">
                        <a class="inst-link secondary" href="{inst_url}/sys.scripts.do" target="_blank">&#9889; Scripts &#8212; Background</a>
                        <a class="inst-link primary" href="{inst_url}/syslog_list.do" target="_blank">&#128203; Syslog</a>
                        <a class="inst-link tertiary" href="{inst_url}/sysauto_script_list.do" target="_blank">&#8987; Scheduled Jobs</a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </td>
        </tr>"""

    if not fixes:
        fix_cards_html = """
        <tr class="row-summary"><td colspan="4">
          <div class="row-inner"><div class="row-area" style="color:var(--green)">&#10003; No remediation required</div></div>
        </td></tr>"""

    # Triage path colour
    path_color = "var(--green)" if "PATH 1" in path else "var(--orange)"
    syslog_color = "var(--green)" if results["syslog_count"] < 5_000_000 else "var(--orange)" if results["syslog_count"] < 20_000_000 else "var(--red)"
    errors_color = "var(--green)" if results["recent_errors"] < 20 else "var(--orange)" if results["recent_errors"] < 100 else "var(--red)"
    toxic_color  = "var(--red)"   if results["toxic_count"] > 0 else "var(--green)"

    # ── CSS (not an f-string — no escaping needed for braces) ─────────────────
    CSS = """
    :root {
      --bg:#0f1117;--surface:#1a1d27;--surface2:#22263a;--surface3:#181b2a;
      --border:#2e3248;--accent:#6c63ff;--accent2:#00d4aa;
      --red:#ff5c5c;--orange:#ffaa44;--yellow:#ffd166;--green:#06d6a0;
      --blue:#4da6ff;--grey:#8b8fa8;--text:#e8eaf6;--text2:#b0b3c6;
    }
    *{box-sizing:border-box;margin:0;padding:0;}
    body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:0 0 80px;}
    .header{background:linear-gradient(135deg,#1a1d27 0%,#12142b 100%);border-bottom:1px solid var(--border);padding:36px 48px 28px;position:relative;overflow:hidden;}
    .header::before{content:'';position:absolute;top:-80px;right:-80px;width:340px;height:340px;background:radial-gradient(circle,rgba(108,99,255,0.13) 0%,transparent 70%);pointer-events:none;}
    .header-top{display:flex;align-items:center;gap:16px;margin-bottom:10px;}
    .logo{width:42px;height:42px;background:linear-gradient(135deg,var(--accent),var(--accent2));border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;}
    .header h1{font-size:22px;font-weight:700;letter-spacing:-0.3px;}
    .header h1 span{color:var(--accent);}
    .header-meta{display:flex;gap:20px;flex-wrap:wrap;font-size:13px;color:var(--text2);}
    .header-meta span{display:flex;align-items:center;gap:6px;}
    .pulse{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 0 0 rgba(6,214,160,0.6);animation:pulse 2s infinite;}
    @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(6,214,160,0.6);}70%{box-shadow:0 0 0 8px rgba(6,214,160,0);}100%{box-shadow:0 0 0 0 rgba(6,214,160,0);}}
    .inst-link-header{display:inline-flex;align-items:center;gap:6px;background:rgba(108,99,255,0.12);border:1px solid rgba(108,99,255,0.3);border-radius:8px;padding:4px 12px;color:var(--accent);font-size:12px;font-weight:500;text-decoration:none;margin-top:14px;transition:background 0.15s;}
    .inst-link-header:hover{background:rgba(108,99,255,0.22);}
    .container{max-width:1120px;margin:0 auto;padding:36px 24px 0;}
    .summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:36px;}
    .card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px 22px;transition:transform 0.18s,box-shadow 0.18s;}
    .card:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,0.4);}
    .card-label{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--grey);margin-bottom:10px;}
    .card-value{font-size:32px;font-weight:700;line-height:1;}
    .card-sub{font-size:12px;color:var(--text2);margin-top:6px;}
    .card.green .card-value{color:var(--green);}.card.orange .card-value{color:var(--orange);}
    .card.accent .card-value{color:var(--accent);}.card.accent2 .card-value{color:var(--accent2);}
    .card.grey .card-value{color:var(--grey);}.card.red .card-value{color:var(--red);}
    .section{margin-bottom:36px;}
    .section-title{font-size:12px;font-weight:600;color:var(--grey);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;}
    .section-title .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);}
    .table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;}
    .status-table{width:100%;border-collapse:collapse;}
    .status-table thead th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.8px;color:var(--grey);padding:11px 18px;border-bottom:1px solid var(--border);background:rgba(0,0,0,0.15);}
    .status-table tbody tr.row-summary td{padding:0;border-bottom:1px solid rgba(46,50,72,0.5);}
    .status-table tbody tr.row-summary:last-child td{border-bottom:none;}
    .row-inner{display:flex;align-items:center;padding:14px 18px;gap:14px;cursor:default;}
    .row-inner.clickable{cursor:pointer;}.row-inner.clickable:hover{background:rgba(108,99,255,0.05);}
    .row-area{flex:2;font-size:14px;font-weight:500;display:flex;align-items:center;gap:10px;}
    .row-status{flex:1.2;}.row-notes{flex:3;font-size:13px;color:var(--text2);}.row-action{flex-shrink:0;}
    .row-chevron{color:var(--grey);font-size:16px;transition:transform 0.22s;flex-shrink:0;margin-left:4px;}
    .expandable-row.open .row-chevron{transform:rotate(180deg);}
    .expand-panel{max-height:0;overflow:hidden;transition:max-height 0.35s ease;}
    .expandable-row.open .expand-panel{max-height:2000px;}
    .expand-inner{border-top:1px solid var(--border);background:var(--surface3);}
    .etabs{display:flex;border-bottom:1px solid var(--border);padding:0 18px;}
    .etab{padding:10px 16px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;color:var(--grey);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:color 0.15s,border-color 0.15s;user-select:none;}
    .etab:hover{color:var(--text2);}.etab.active{color:var(--accent);border-color:var(--accent);}
    .epanel{display:none;padding:20px 22px 24px;}.epanel.active{display:block;}
    .elabel{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--grey);margin-bottom:8px;}
    .edesc{font-size:14px;color:var(--text2);line-height:1.65;}
    .steps{list-style:none;counter-reset:s;margin-top:4px;}
    .steps li{counter-increment:s;display:flex;gap:12px;font-size:14px;color:var(--text2);line-height:1.6;margin-bottom:10px;align-items:flex-start;}
    .steps li::before{content:counter(s);display:flex;align-items:center;justify-content:center;min-width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;font-size:11px;font-weight:700;margin-top:1px;flex-shrink:0;}
    .script-label-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}
    .copy-btn{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:6px;background:rgba(108,99,255,0.15);border:1px solid rgba(108,99,255,0.3);color:var(--accent);font-size:12px;font-weight:600;cursor:pointer;transition:background 0.15s;user-select:none;}
    .copy-btn:hover{background:rgba(108,99,255,0.28);}.copy-btn.copied{background:rgba(6,214,160,0.15);border-color:rgba(6,214,160,0.3);color:var(--green);}
    pre.script{background:#090c16;border:1px solid var(--border);border-radius:10px;padding:16px 18px;overflow-x:auto;font-family:'Courier New',monospace;font-size:13px;color:#a9d4ff;line-height:1.7;tab-size:2;white-space:pre-wrap;word-break:break-word;}
    .links-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
    .inst-link{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:8px;font-size:13px;font-weight:500;text-decoration:none;transition:all 0.15s;border:1px solid;}
    .inst-link.primary{background:rgba(108,99,255,0.15);border-color:rgba(108,99,255,0.4);color:var(--accent);}
    .inst-link.primary:hover{background:rgba(108,99,255,0.28);}
    .inst-link.secondary{background:rgba(0,212,170,0.1);border-color:rgba(0,212,170,0.3);color:var(--accent2);}
    .inst-link.secondary:hover{background:rgba(0,212,170,0.2);}
    .inst-link.tertiary{background:rgba(139,143,168,0.1);border-color:rgba(139,143,168,0.25);color:var(--grey);}
    .inst-link.tertiary:hover{background:rgba(139,143,168,0.18);color:var(--text2);}
    .badge{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;white-space:nowrap;}
    .badge.healthy{background:rgba(6,214,160,0.12);color:var(--green);}
    .badge.warning{background:rgba(255,170,68,0.12);color:var(--orange);}
    .badge.error{background:rgba(255,92,92,0.12);color:var(--red);}
    .badge.idle{background:rgba(139,143,168,0.12);color:var(--grey);}
    .badge.info{background:rgba(108,99,255,0.12);color:var(--accent);}
    .sev-bar{width:4px;flex-shrink:0;align-self:stretch;}
    .sev-error{background:var(--red);}.sev-warning{background:var(--orange);}.sev-check{background:var(--blue);}
    code{font-family:'Courier New',monospace;background:rgba(108,99,255,0.12);color:var(--accent2);border-radius:4px;padding:1px 6px;font-size:12.5px;}
    .footer{text-align:center;padding-top:52px;font-size:12px;color:var(--grey);}
    .footer a{color:var(--accent);text-decoration:none;}
    ::-webkit-scrollbar{width:5px;height:5px;}::-webkit-scrollbar-track{background:var(--bg);}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}
    """

    JS = """
    function toggleRow(id) {
      document.getElementById(id).classList.toggle('open');
    }
    function switchTab(event, prefix, tabName) {
      event.stopPropagation();
      var container = event.target.closest('.expand-inner');
      container.querySelectorAll('.etab').forEach(function(t){t.classList.remove('active');});
      container.querySelectorAll('.epanel').forEach(function(p){p.classList.remove('active');});
      event.target.classList.add('active');
      var panel = document.getElementById(prefix + '-' + tabName);
      if (panel) panel.classList.add('active');
    }
    function copyScript(id) {
      var el = document.getElementById(id);
      if (!el) return;
      navigator.clipboard.writeText(el.innerText || el.textContent).then(function() {
        var btn = el.closest('.epanel').querySelector('.copy-btn');
        if (btn) {
          btn.textContent = '\\u2713 Copied!';
          btn.classList.add('copied');
          setTimeout(function(){ btn.innerHTML = '&#128203; Copy'; btn.classList.remove('copied'); }, 2000);
        }
      });
    }
    """

    # ── Assemble ──────────────────────────────────────────────────────────────
    unhealthy_count = sum(1 for c in checks if is_unhealthy(c["status"]))
    grade_card_class = "green" if grade in ("EXCELLENT","GOOD") else "orange" if grade == "FAIR" else "red"

    html = (
        f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        f'<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>\n'
        f'<title>Health Check \u2014 {instance_name}</title>\n'
        f'<style>{CSS}</style>\n</head>\n<body>\n'

        # Header
        f'<div class="header">'
        f'<div class="header-top"><div class="logo">\U0001f50d</div>'
        f'<h1>Health Check \u2014 <span>{instance_name}</span></h1></div>'
        f'<div class="header-meta">'
        f'<span><div class="pulse"></div>&nbsp;Instance Online</span>'
        f'<span>\U0001f4c5 {run_time}</span>'
        f'<span>\U0001f3f7\ufe0f ServiceNow Admin Bot v1.0</span>'
        f'</div>'
        f'<a class="inst-link-header" href="{inst_url}" target="_blank">\U0001f517 Open Instance &nbsp;{instance_name}</a>'
        f'</div>\n'

        # Container open
        f'<div class="container">\n'

        # Summary cards
        f'<div class="summary-grid">'
        f'<div class="card {grade_card_class}"><div class="card-label">Performance Grade</div><div class="card-value">{grade}</div><div class="card-sub">{total_ms}ms benchmark</div></div>'
        f'<div class="card {"green" if results["syslog_count"] < 5_000_000 else "orange" if results["syslog_count"] < 20_000_000 else "red"}"><div class="card-label">Syslog Records</div><div class="card-value">{fmt(results["syslog_count"])}</div><div class="card-sub">Warn &gt;5M · Fail &gt;20M</div></div>'
        f'<div class="card {"green" if results["recent_errors"] < 20 else "orange" if results["recent_errors"] < 100 else "red"}"><div class="card-label">Errors (5 min)</div><div class="card-value">{fmt(results["recent_errors"])}</div><div class="card-sub">Warn &gt;20 · Fail &gt;100</div></div>'
        f'<div class="card {"red" if results["toxic_count"] > 0 else "green"}"><div class="card-label">Toxic Jobs</div><div class="card-value">{results["toxic_count"]}</div><div class="card-sub">Sub-60s scheduled jobs</div></div>'
        f'<div class="card {"orange" if unhealthy_count > 0 else "green"}"><div class="card-label">Issues Found</div><div class="card-value">{unhealthy_count}</div><div class="card-sub">Checks needing attention</div></div>'
        f'<div class="card {"orange" if fixes else "green"}"><div class="card-label">Fix Items</div><div class="card-value">{len(fixes)}</div><div class="card-sub">Remediation recommended</div></div>'
        f'</div>\n'

        # Triage summary
        f'<div class="section"><div class="section-title"><div class="dot"></div> Phase 1 \u2014 Triage Decision</div>'
        f'<div class="table-wrap" style="padding:20px 24px;">'
        f'<div style="font-size:13px;color:var(--text2);margin-bottom:16px;">Decision: <strong style="color:{path_color}">{path}</strong></div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;text-align:center;">'
        f'<div><div style="font-size:28px;font-weight:700;color:{syslog_color}">{fmt(results["syslog_count"])}</div><div style="font-size:12px;color:var(--grey);margin-top:4px;">Syslog Records</div></div>'
        f'<div><div style="font-size:28px;font-weight:700;color:{errors_color}">{fmt(results["recent_errors"])}</div><div style="font-size:12px;color:var(--grey);margin-top:4px;">Errors (5 min)</div></div>'
        f'<div><div style="font-size:28px;font-weight:700;color:{toxic_color}">{results["toxic_count"]}</div><div style="font-size:12px;color:var(--grey);margin-top:4px;">Toxic Jobs</div></div>'
        f'</div></div></div>\n'

        # Database Tier table
        f'<div class="section"><div class="section-title"><div class="dot"></div> Phase 2 \u2014 Database Tier (D1\u2013D7) \u2014 click any non-healthy row to expand</div>'
        f'<div class="table-wrap"><table class="status-table">'
        f'<thead><tr><th style="width:30%">Check</th><th style="width:14%">Status</th><th>Notes</th><th style="width:32px"></th></tr></thead>'
        f'<tbody>{db_rows}</tbody></table></div></div>\n'

        # Application Tier table
        f'<div class="section"><div class="section-title"><div class="dot"></div> Phase 2 \u2014 Application Tier (A1\u2013A4)</div>'
        f'<div class="table-wrap"><table class="status-table">'
        f'<thead><tr><th style="width:30%">Check</th><th style="width:14%">Status</th><th>Notes</th><th style="width:32px"></th></tr></thead>'
        f'<tbody>{app_rows}</tbody></table></div></div>\n'

        # Benchmark
        f'<div class="section"><div class="section-title"><div class="dot"></div> Phase 3 \u2014 Transaction Tier Benchmark (5 runs each)</div>'
        f'<div class="table-wrap"><table class="status-table">'
        f'<thead><tr><th>Query</th><th style="text-align:right;width:140px">Avg (5 runs)</th><th style="text-align:right;width:140px">Variance</th></tr></thead>'
        f'<tbody>{bench_rows_html}</tbody>'
        f'<tfoot><tr><td style="padding:13px 16px;font-size:14px;font-weight:600;background:rgba(0,0,0,0.15)">Total Score</td>'
        f'<td style="padding:13px 16px;text-align:right;font-size:18px;font-weight:700;background:rgba(0,0,0,0.15);color:{grade_color}">{total_ms}ms</td>'
        f'<td style="padding:13px 16px;text-align:right;font-weight:700;background:rgba(0,0,0,0.15);color:{grade_color}">{grade}</td></tr></tfoot>'
        f'</table></div></div>\n'

        # Fix Recommendations
        f'<div class="section"><div class="section-title"><div class="dot"></div> Fix Recommendations ({len(fixes)})</div>'
        f'<div class="table-wrap"><table class="status-table">'
        f'<thead><tr><th style="width:30%">Issue</th><th style="width:14%">Priority</th><th>Description</th><th style="width:32px"></th></tr></thead>'
        f'<tbody>{fix_cards_html}</tbody></table></div></div>\n'

        # Footer
        f'<div class="footer">Generated by <a href="https://claude.ai/claude-code" target="_blank">Claude Code</a>'
        f' &nbsp;&middot;&nbsp; ServiceNow Admin Bot v1.0 &nbsp;&middot;&nbsp; All checks are read-only GET requests &nbsp;&middot;&nbsp; {run_time}'
        f' &nbsp;&middot;&nbsp; <a href="{inst_url}" target="_blank">{instance_name}</a></div>\n'

        # Container close + JS
        f'</div>\n<script>{JS}</script>\n</body>\n</html>'
    )

    return html


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        INSTANCE, USERNAME, PASSWORD = load_credentials()
        instance_name = INSTANCE.replace("https://", "").replace("http://", "")

        init_session(USERNAME, PASSWORD)

        # Quick connection test
        print(f"\nConnecting to {instance_name}...", end=" ", flush=True)
        test = sn_count("syslog")
        if test < 0:
            print("FAILED\n")
            print("ERROR: Could not connect. Check your credentials and instance URL.")
            print("Common causes: wrong password, instance hibernated, no VPN.")
            sys.exit(1)
        print("OK\n")

        run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results = run_health_check()

        html = build_html_report(results, instance_name, run_time)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        clean_name = instance_name.split(".")[0]
        filename = f"healthcheck_{clean_name}_{timestamp}.html"
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Report saved: {filename}")
        print("Opening in browser...\n")
        webbrowser.open(f"file://{output_path}")

    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
