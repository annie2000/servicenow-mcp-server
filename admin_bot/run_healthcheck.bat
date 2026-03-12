@echo off
REM ============================================================
REM ServiceNow Admin Bot — Windows Launcher
REM ============================================================
REM Usage:
REM   Double-click this file
REM   OR run from command prompt:
REM   run_healthcheck.bat yourinstance.service-now.com admin password
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   ServiceNow Admin Bot -- Instance Health Check
echo ============================================================

REM ── Find Python 3 ─────────────────────────────────────────
set PYTHON=

for %%p in (python3 python py) do (
    if "!PYTHON!"=="" (
        %%p --version >nul 2>&1
        if !errorlevel! equ 0 (
            for /f "tokens=2" %%v in ('%%p --version 2^>^&1') do (
                set VER=%%v
            )
            set PYTHON=%%p
        )
    )
)

if "%PYTHON%"=="" (
    echo.
    echo ERROR: Python 3.8 or higher is required but not found.
    echo.
    echo Install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo   Python : %PYTHON% (%VER%)

REM ── Install requests if missing ───────────────────────────
%PYTHON% -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo   Installing: requests library...
    %PYTHON% -m pip install requests --quiet
)

set SCRIPT_DIR=%~dp0
echo   Script : %SCRIPT_DIR%healthcheck.py
echo ============================================================
echo.

REM ── Run ───────────────────────────────────────────────────
if "%~3"=="" (
    %PYTHON% "%SCRIPT_DIR%healthcheck.py"
) else (
    %PYTHON% "%SCRIPT_DIR%healthcheck.py" %1 %2 %3
)

if errorlevel 1 (
    echo.
    echo Health check finished with errors. See output above.
    pause
)
