#!/bin/bash
# ============================================================
# ServiceNow Admin Bot — Mac/Linux Launcher
# ============================================================
# Usage:
#   bash run_healthcheck.sh
#   bash run_healthcheck.sh yourinstance.service-now.com admin password
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/healthcheck.py"

echo ""
echo "============================================================"
echo "  ServiceNow Admin Bot — Instance Health Check"
echo "============================================================"

# ── Find Python 3 ────────────────────────────────────────────
PYTHON=""
for cmd in python3 python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3.8; do
    if command -v "$cmd" &>/dev/null; then
        VERSION=$("$cmd" --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo "$VERSION" | cut -d. -f1)
        MINOR=$(echo "$VERSION" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "ERROR: Python 3.8 or higher is required but not found."
    echo ""
    echo "Install Python:"
    echo "  Mac (Homebrew):  brew install python3"
    echo "  Or download from: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo "  Python : $PYTHON ($("$PYTHON" --version 2>&1))"

# ── Install requests if missing ──────────────────────────────
if ! "$PYTHON" -c "import requests" &>/dev/null 2>&1; then
    echo "  Installing: requests library..."
    "$PYTHON" -m pip install requests --quiet
fi

echo "  Script : $PYTHON_SCRIPT"
echo "============================================================"
echo ""

# ── Run ──────────────────────────────────────────────────────
if [ $# -eq 3 ]; then
    "$PYTHON" "$PYTHON_SCRIPT" "$1" "$2" "$3"
else
    "$PYTHON" "$PYTHON_SCRIPT"
fi
