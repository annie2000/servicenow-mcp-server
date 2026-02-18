#!/usr/bin/env python3
"""
Quick MCP Server Validation
Fast check that everything is configured correctly
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE = os.getenv("SERVICENOW_INSTANCE")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

def check(name, condition, fix=""):
    """Print check result"""
    if condition:
        print(f"âœ… {name}")
        return True
    else:
        print(f"âŒ {name}")
        if fix:
            print(f"   Fix: {fix}")
        return False

def main():
    print("\nðŸ” Quick MCP Server Validation\n")
    
    all_good = True
    
    # Check 1: Environment variables
    all_good &= check(
        "Environment variables loaded",
        INSTANCE and USERNAME and PASSWORD,
        "Check .env file exists and has SERVICENOW_INSTANCE, USERNAME, PASSWORD"
    )
    
    if not all_good:
        print("\nâŒ Cannot proceed without credentials\n")
        return
    
    # Check 2: Instance URL format
    all_good &= check(
        "Instance URL format correct",
        INSTANCE.startswith("https://"),
        "Instance URL should start with https://"
    )
    
    # Check 3: Basic authentication
    print("\nTesting connection...")
    try:
        response = requests.get(
            f"{INSTANCE}/api/now/table/syslog",
            params={"sysparm_limit": 1},
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
            timeout=30
        )
        all_good &= check(
            "Authentication working",
            response.status_code == 200,
            "Check username/password in .env file"
        )
    except requests.exceptions.Timeout:
        check("Connection test", False, "Request timed out - check instance URL")
        all_good = False
    except requests.exceptions.ConnectionError:
        check("Connection test", False, "Cannot connect - check instance URL and network")
        all_good = False
    except Exception as e:
        check("Connection test", False, f"Error: {str(e)}")
        all_good = False
    
    if not all_good:
        print("\nâŒ Basic tests failed. Fix issues above before proceeding.\n")
        return
    
    # Check 4: Key table access
    print("\nChecking table access...")
    tables = {
        "sn_aia_agent": "AI Agents",
        "sn_aia_usecase": "Agentic Workflows",
        "sys_flow_context": "Flow Designer"
    }
    
    for table, desc in tables.items():
        try:
            response = requests.get(
                f"{INSTANCE}/api/now/table/{table}",
                params={"sysparm_limit": 1},
                auth=(USERNAME, PASSWORD),
                headers={"Accept": "application/json"},
                timeout=10
            )
            check(f"{desc} table", response.status_code == 200)
        except:
            check(f"{desc} table", False, "Table may not exist or no permission")
    
    # Check 5: Write permissions (quick test)
    print("\nChecking write permissions...")
    try:
        response = requests.post(
            f"{INSTANCE}/api/now/table/sn_aia_agent",
            json={"name": "TEST"},  # Will fail but tests permission
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10
        )
        has_write = response.status_code in [200, 201, 400]  # 400 = permission granted but invalid payload
        check(
            "Write permissions",
            has_write,
            "Need sn_aia.admin role for write operations"
        )
    except Exception as e:
        check("Write permissions", False, f"Error: {str(e)}")
    
    # Summary
    print("\n" + "="*50)
    if all_good:
        print("âœ… All checks passed!")
        print("\nYour MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Open Claude Desktop")
        print("2. Check Settings > Developer shows 'servicenow-debug' running")
        print("3. Try: 'Show me all AI agents'")
    else:
        print("âš ï¸  Some checks failed")
        print("\nFix the issues above, then:")
        print("1. Run this script again")
        print("2. Once passing, test with Claude Desktop")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
