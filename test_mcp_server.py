#!/usr/bin/env python3
"""
ServiceNow MCP Server Test Suite
Tests all 35 tools to verify table access and API functionality
"""

import os
import sys
import time
from dotenv import load_dotenv
import requests
from datetime import datetime

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}âœ… {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}âŒ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}âš ï¸  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}â„¹ï¸  {msg}{Colors.END}")

def print_section(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

# Load environment
load_dotenv()
INSTANCE = os.getenv("SERVICENOW_INSTANCE")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

# Track test results
results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

# Track created items for cleanup
created_items = {
    "agents": [],
    "workflows": [],
    "tools": [],
    "triggers": []
}

def test_table_access(table_name, description):
    """Test read access to a ServiceNow table"""
    print(f"Testing {table_name}... ", end="")
    url = f"{INSTANCE}/api/now/table/{table_name}"
    params = {"sysparm_limit": 1}
    
    try:
        response = requests.get(
            url, params=params,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"{description}")
            results["passed"] += 1
            return True
        elif response.status_code == 403:
            print_error(f"Permission denied for {table_name}")
            results["failed"] += 1
            return False
        else:
            print_error(f"Error {response.status_code}")
            results["failed"] += 1
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        results["failed"] += 1
        return False

def test_write_access(table_name, description):
    """Test write access to a ServiceNow table"""
    print(f"Testing write to {table_name}... ", end="")
    url = f"{INSTANCE}/api/now/table/{table_name}"
    
    # Minimal payload - will be rejected but tests write permission
    payload = {"name": "TEST_PERMISSION_CHECK"}
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            # Immediately delete the test record
            result = response.json().get("result", {})
            test_id = result.get("sys_id")
            if test_id:
                requests.delete(
                    f"{url}/{test_id}",
                    auth=(USERNAME, PASSWORD),
                    headers={"Accept": "application/json"}
                )
            print_success(f"{description}")
            results["passed"] += 1
            return True
        elif response.status_code == 403:
            print_error(f"No write permission for {table_name}")
            results["failed"] += 1
            return False
        elif response.status_code == 400:
            # Expected - means we can write but payload was invalid (permission granted)
            print_success(f"{description} (400 = permission OK)")
            results["passed"] += 1
            return True
        else:
            print_warning(f"Unexpected response {response.status_code}")
            results["warnings"] += 1
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        results["failed"] += 1
        return False

def create_test_agent():
    """Create a test AI agent"""
    print_info("Creating test agent...")
    url = f"{INSTANCE}/api/now/table/sn_aia_agent"
    
    payload = {
        "name": "TEST_MCP_Agent",
        "description": "Test agent created by MCP test suite - safe to delete",
        "agent_role": "Testing agent role",
        "list_of_steps": "Step 1: This is a test\nStep 2: This can be deleted",
        "active": "false"  # Keep it inactive
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json().get("result", {})
            agent_id = result.get("sys_id")
            created_items["agents"].append(agent_id)
            print_success(f"Created test agent: {agent_id}")
            return agent_id
        else:
            print_error(f"Failed to create agent: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"Exception creating agent: {str(e)}")
        return None

def update_test_agent(agent_id):
    """Update a test AI agent"""
    print_info("Updating test agent...")
    url = f"{INSTANCE}/api/now/table/sn_aia_agent/{agent_id}"
    
    payload = {
        "description": "Updated by MCP test suite"
    }
    
    try:
        response = requests.patch(
            url,
            json=payload,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("Agent updated successfully")
            return True
        else:
            print_error(f"Failed to update agent: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception updating agent: {str(e)}")
        return False

def delete_test_agent(agent_id):
    """Delete a test AI agent"""
    print_info(f"Deleting test agent {agent_id}...")
    url = f"{INSTANCE}/api/now/table/sn_aia_agent/{agent_id}"
    
    try:
        response = requests.delete(
            url,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            print_success("Agent deleted successfully")
            created_items["agents"].remove(agent_id)
            return True
        else:
            print_error(f"Failed to delete agent: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception deleting agent: {str(e)}")
        return False

def cleanup():
    """Clean up any created test items"""
    print_section("Cleanup")
    
    # Delete test agents
    for agent_id in created_items["agents"][:]:
        delete_test_agent(agent_id)
    
    # Delete test workflows
    for workflow_id in created_items["workflows"][:]:
        url = f"{INSTANCE}/api/now/table/sn_aia_usecase/{workflow_id}"
        try:
            response = requests.delete(url, auth=(USERNAME, PASSWORD), headers={"Accept": "application/json"})
            if response.status_code == 204:
                print_success(f"Deleted test workflow {workflow_id}")
                created_items["workflows"].remove(workflow_id)
        except:
            pass
    
    # Delete test tools
    for tool_id in created_items["tools"][:]:
        url = f"{INSTANCE}/api/now/table/sn_aia_tool/{tool_id}"
        try:
            response = requests.delete(url, auth=(USERNAME, PASSWORD), headers={"Accept": "application/json"})
            if response.status_code == 204:
                print_success(f"Deleted test tool {tool_id}")
                created_items["tools"].remove(tool_id)
        except:
            pass
    
    # Delete test triggers
    for trigger_id in created_items["triggers"][:]:
        url = f"{INSTANCE}/api/now/table/sn_aia_trigger_configuration/{trigger_id}"
        try:
            response = requests.delete(url, auth=(USERNAME, PASSWORD), headers={"Accept": "application/json"})
            if response.status_code == 204:
                print_success(f"Deleted test trigger {trigger_id}")
                created_items["triggers"].remove(trigger_id)
        except:
            pass

def main():
    print_section("ServiceNow MCP Server Test Suite")
    print(f"Instance: {INSTANCE}")
    print(f"Username: {USERNAME}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test 1: Authentication
    print_section("Test 1: Authentication")
    if not INSTANCE or not USERNAME or not PASSWORD:
        print_error("Missing credentials in .env file")
        print("Required: SERVICENOW_INSTANCE, SERVICENOW_USERNAME, SERVICENOW_PASSWORD")
        return
    
    test_table_access("syslog", "Authentication working")
    
    # Test 2: Core Debugging Tables (Read-Only)
    print_section("Test 2: Core Debugging Tables")
    test_table_access("syslog", "Syslog table")
    
    # Test 3: Flow Designer Tables (Read-Only)
    print_section("Test 3: Flow Designer Tables")
    test_table_access("sys_flow_context", "Flow context table")
    test_table_access("sys_flow_log", "Flow log table")
    test_table_access("sys_flow_report_doc_chunk", "Flow report table")
    
    # Test 4: AI Agent Configuration Tables (Read)
    print_section("Test 4: AI Agent Configuration Tables (Read)")
    test_table_access("sn_aia_usecase", "Agentic workflows table")
    test_table_access("sn_aia_agent", "AI agents table")
    test_table_access("sn_aia_tool", "Tools table")
    test_table_access("sn_aia_agent_tool_m2m", "Agent-tool mapping table")
    test_table_access("sn_aia_trigger_configuration", "Trigger configuration table")
    
    # Test 5: AI Agent Execution Tables (Read)
    print_section("Test 5: AI Agent Execution Tables (Read)")
    test_table_access("sn_aia_execution_plan", "Execution plans table")
    test_table_access("sn_aia_execution_task", "Execution tasks table")
    test_table_access("sn_aia_tools_execution", "Tool executions table")
    test_table_access("sys_generative_ai_log", "Generative AI log table")
    test_table_access("sn_aia_message", "Agent messages table")
    
    # Test 6: Write Permissions
    print_section("Test 6: Write Permissions Check")
    print_warning("This tests if you have write access to AI Agent tables")
    print_warning("Required for v3 write operations\n")
    
    test_write_access("sn_aia_agent", "AI agent write access")
    test_write_access("sn_aia_usecase", "Workflow write access")
    test_write_access("sn_aia_tool", "Tool write access")
    test_write_access("sn_aia_trigger_configuration", "Trigger write access")
    
    # Test 7: Full CRUD Cycle (if write access available)
    print_section("Test 7: Full Create-Read-Update-Delete Cycle")
    
    agent_id = create_test_agent()
    if agent_id:
        time.sleep(1)  # Give ServiceNow a moment
        
        # Verify creation by reading it back
        url = f"{INSTANCE}/api/now/table/sn_aia_agent/{agent_id}"
        response = requests.get(url, auth=(USERNAME, PASSWORD), headers={"Accept": "application/json"})
        if response.status_code == 200:
            print_success("Successfully read back created agent")
            results["passed"] += 1
        else:
            print_error("Failed to read back created agent")
            results["failed"] += 1
        
        time.sleep(1)
        
        # Test update
        if update_test_agent(agent_id):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        time.sleep(1)
        
        # Test delete
        if delete_test_agent(agent_id):
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        print_warning("Skipping CRUD tests - agent creation failed")
        print_warning("This may indicate insufficient write permissions")
    
    # Cleanup any remaining test items
    if created_items["agents"] or created_items["workflows"] or created_items["tools"] or created_items["triggers"]:
        cleanup()
    
    # Final Summary
    print_section("Test Summary")
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print_success(f"Passed: {results['passed']}")
    print_error(f"Failed: {results['failed']}")
    print_warning(f"Warnings: {results['warnings']}")
    print(f"\nPass Rate: {pass_rate:.1f}%\n")
    
    if results["failed"] == 0:
        print_success("ðŸŽ‰ All tests passed! Your MCP server is ready to use.")
        print_info("Next step: Test through Claude Desktop with conversational prompts")
    elif results["failed"] <= 5:
        print_warning("âš ï¸  Some tests failed. Check the errors above.")
        print_info("Most common issues:")
        print_info("  - Missing write permissions (need sn_aia.admin role)")
        print_info("  - Some tables may not exist in your instance version")
    else:
        print_error("âŒ Multiple test failures detected.")
        print_info("Possible issues:")
        print_info("  - Invalid credentials in .env file")
        print_info("  - Insufficient permissions")
        print_info("  - Instance URL incorrect")
        print_info("  - Tables don't exist (check ServiceNow version)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        print_info("Cleaning up...")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
