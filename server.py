import os
from dotenv import load_dotenv
load_dotenv()

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("servicenow-debug")

INSTANCE = os.getenv("SERVICENOW_INSTANCE")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

# ============================================================================
# ORIGINAL SYSLOG TOOL
# ============================================================================

@mcp.tool()
def query_syslog(
    message_contains: str = "",
    source: str = "",
    level: str = "",
    limit: int = 20,
    minutes_ago: int = 60
) -> str:
    """
    Query the ServiceNow syslog table for debugging.
    
    Args:
        message_contains: Filter by message text
        source: Filter by source
        level: Filter by log level (error, warn, info, etc.)
        limit: Max number of records to return (default 20)
        minutes_ago: Only show logs from last N minutes (default 60)
    """
    query_parts = []
    if message_contains:
        query_parts.append(f"messageLIKE{message_contains}")
    if source:
        query_parts.append(f"sourceLIKE{source}")
    if level:
        query_parts.append(f"level={level}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/syslog"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_created_on,level,source,message"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No syslog entries found matching your criteria."

    output = []
    for entry in results:
        output.append(
            f"[{entry.get('sys_created_on')}] "
            f"{entry.get('level', 'N/A').upper()} | "
            f"{entry.get('source', 'N/A')}\n"
            f"{entry.get('message', 'No message')}\n"
        )
    return "\n---\n".join(output)


# ============================================================================
# FLOW DESIGNER EXECUTION TOOLS
# ============================================================================

@mcp.tool()
def query_flow_contexts(
    flow_name: str = "",
    status: str = "",
    minutes_ago: int = 60,
    limit: int = 20
) -> str:
    """
    Query Flow Designer execution contexts (sys_flow_context).
    Shows high-level flow execution summary including run time, status, and duration.
    
    Args:
        flow_name: Filter by flow name
        status: Filter by status (success, error, waiting, cancelled, etc.)
        minutes_ago: Only show executions from last N minutes (default 60)
        limit: Max number of records to return (default 20)
    """
    query_parts = []
    if flow_name:
        query_parts.append(f"flow.nameLIKE{flow_name}")
    if status:
        query_parts.append(f"status={status}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sys_flow_context"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,flow.name,status,started,ended,duration,output,sys_created_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No flow contexts found matching your criteria."

    output = []
    for ctx in results:
        output.append(
            f"Flow: {ctx.get('flow.name', 'N/A')}\n"
            f"Context ID: {ctx.get('sys_id')}\n"
            f"Status: {ctx.get('status', 'N/A')}\n"
            f"Started: {ctx.get('started', 'N/A')}\n"
            f"Ended: {ctx.get('ended', 'N/A')}\n"
            f"Duration: {ctx.get('duration', 'N/A')} seconds\n"
            f"Created: {ctx.get('sys_created_on', 'N/A')}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def query_flow_logs(
    flow_context_id: str = "",
    level: str = "",
    message_contains: str = "",
    minutes_ago: int = 60,
    limit: int = 50
) -> str:
    """
    Query Flow Designer detailed logs (sys_flow_log).
    Captures detailed logs for Flow Designer actions.
    
    Args:
        flow_context_id: Filter by specific flow context sys_id
        level: Filter by log level (error, warn, info, debug)
        message_contains: Filter by message text
        minutes_ago: Only show logs from last N minutes (default 60)
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if flow_context_id:
        query_parts.append(f"context={flow_context_id}")
    if level:
        query_parts.append(f"level={level}")
    if message_contains:
        query_parts.append(f"messageLIKE{message_contains}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sys_flow_log"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,context,level,message,action,sys_created_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No flow logs found matching your criteria."

    output = []
    for log in results:
        output.append(
            f"[{log.get('sys_created_on')}] {log.get('level', 'N/A').upper()}\n"
            f"Context: {log.get('context', 'N/A')}\n"
            f"Action: {log.get('action', 'N/A')}\n"
            f"Message: {log.get('message', 'N/A')}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def get_flow_context_details(
    flow_context_id: str
) -> str:
    """
    Get complete details of a flow execution including its logs.
    
    Args:
        flow_context_id: Sys ID of the flow context to investigate
    """
    # Get flow context
    ctx_url = f"{INSTANCE}/api/now/table/sys_flow_context/{flow_context_id}"
    params = {
        "sysparm_fields": "sys_id,flow.name,status,started,ended,duration,output,inputs,sys_created_on"
    }

    ctx_response = requests.get(
        ctx_url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if ctx_response.status_code != 200:
        return f"Error: {ctx_response.status_code} - {ctx_response.text}"

    ctx = ctx_response.json().get("result", {})
    if not ctx:
        return "Flow context not found."

    output = [
        "=== FLOW CONTEXT DETAILS ===",
        f"Flow: {ctx.get('flow.name', 'N/A')}",
        f"Context ID: {ctx.get('sys_id')}",
        f"Status: {ctx.get('status', 'N/A')}",
        f"Started: {ctx.get('started', 'N/A')}",
        f"Ended: {ctx.get('ended', 'N/A')}",
        f"Duration: {ctx.get('duration', 'N/A')} seconds",
        f"Created: {ctx.get('sys_created_on', 'N/A')}"
    ]
    
    inputs = ctx.get('inputs', '')
    if inputs:
        output.append(f"\nInputs: {inputs[:500]}")
    
    flow_output = ctx.get('output', '')
    if flow_output:
        output.append(f"\nOutput: {flow_output[:500]}")

    # Get flow logs for this context
    log_url = f"{INSTANCE}/api/now/table/sys_flow_log"
    log_params = {
        "sysparm_query": f"context={flow_context_id}^ORDERBYsys_created_on",
        "sysparm_limit": 100,
        "sysparm_fields": "level,message,action,sys_created_on"
    }

    log_response = requests.get(
        log_url, params=log_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if log_response.status_code == 200:
        logs = log_response.json().get("result", [])
        if logs:
            output.append("\n=== FLOW LOGS ===")
            for i, log in enumerate(logs, 1):
                level = log.get('level', 'N/A')
                output.append(
                    f"{i}. [{log.get('sys_created_on')}] {level.upper()}\n"
                    f"   Action: {log.get('action', 'N/A')}\n"
                    f"   Message: {log.get('message', 'N/A')}"
                )
        else:
            output.append("\n=== FLOW LOGS ===\nNo logs found")

    return "\n".join(output)


@mcp.tool()
def query_generative_ai_logs_detailed(
    minutes_ago: int = 60,
    limit: int = 20,
    execution_plan_id: str = ""
) -> str:
    """
    Query the sys_generative_ai_log table with FULL field access for detailed AI/LLM debugging.
    This gets ALL fields including error messages, request/response data, and execution details.
    
    Args:
        minutes_ago: Only show logs from last N minutes (default 60)
        limit: Max number of records to return (default 20)
        execution_plan_id: Filter by specific execution plan sys_id (optional)
    """
    query_parts = []
    if execution_plan_id:
        query_parts.append(f"execution_plan={execution_plan_id}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sys_generative_ai_log"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_display_value": "false"  # Get raw values
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No generative AI logs found matching your criteria."

    output = []
    for log in results:
        entry = [
            f"=== GENERATIVE AI LOG ===",
            f"Created: {log.get('sys_created_on')}",
            f"Sys ID: {log.get('sys_id')}",
            f"Capability: {log.get('capability', 'N/A')}",
            f"Model: {log.get('model', 'N/A')}",
            f"Status: {log.get('status', 'N/A')}",
            f"Execution Plan: {log.get('execution_plan', 'N/A')}",
            f"Provider: {log.get('provider', 'N/A')}",
            f"Input Tokens: {log.get('input_tokens', 'N/A')}",
            f"Output Tokens: {log.get('output_tokens', 'N/A')}",
            f"Total Tokens: {log.get('total_tokens', 'N/A')}",
            f"Duration (ms): {log.get('duration_ms', 'N/A')}",
        ]
        
        # Add error information if present
        if log.get('error_message'):
            entry.append(f"ERROR MESSAGE: {log.get('error_message')}")
        if log.get('error_code'):
            entry.append(f"ERROR CODE: {log.get('error_code')}")
        if log.get('error_details'):
            entry.append(f"ERROR DETAILS: {log.get('error_details')[:500]}")
        
        # Add request/response data (truncated)
        if log.get('request'):
            entry.append(f"\nREQUEST (first 500 chars):\n{str(log.get('request'))[:500]}")
        if log.get('response'):
            entry.append(f"\nRESPONSE (first 500 chars):\n{str(log.get('response'))[:500]}")
            
        output.append("\n".join(entry))
    
    return "\n\n---\n\n".join(output)


@mcp.tool()
def query_flow_reports(
    flow_context_id: str = "",
    minutes_ago: int = 60,
    limit: int = 20
) -> str:
    """
    Query Flow Designer reporting data (sys_flow_report_doc_chunk).
    Stores detailed runtime states, inputs, and outputs for flows.
    
    Args:
        flow_context_id: Filter by specific flow context sys_id
        minutes_ago: Only show reports from last N minutes (default 60)
        limit: Max number of records to return (default 20)
    """
    query_parts = []
    if flow_context_id:
        query_parts.append(f"context={flow_context_id}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sys_flow_report_doc_chunk"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,context,data,sys_created_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No flow report chunks found matching your criteria."

    output = []
    for report in results:
        data = report.get('data', '')
        output.append(
            f"Report ID: {report.get('sys_id')}\n"
            f"Context: {report.get('context', 'N/A')}\n"
            f"Created: {report.get('sys_created_on', 'N/A')}\n"
            f"Data (first 500 chars): {data[:500]}"
        )
    return "\n\n---\n\n".join(output)


# ============================================================================
# AI AGENT CONFIGURATION TOOLS
# ============================================================================

@mcp.tool()
def list_agentic_workflows(
    active_only: bool = True,
    limit: int = 50
) -> str:
    """
    List all agentic workflows (use cases) configured in the system.
    
    Args:
        active_only: Only show active workflows (default True)
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if active_only:
        query_parts.append("active=true")
    query = "^".join(query_parts) if query_parts else ""
    
    url = f"{INSTANCE}/api/now/table/sn_aia_usecase"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on" if query else "ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,name,description,active,state,sys_created_on,sys_updated_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No agentic workflows found."

    output = []
    for wf in results:
        output.append(
            f"Name: {wf.get('name', 'N/A')}\n"
            f"Sys ID: {wf.get('sys_id')}\n"
            f"Active: {wf.get('active', 'N/A')}\n"
            f"State: {wf.get('state', 'N/A')}\n"
            f"Description: {wf.get('description', 'N/A')}\n"
            f"Created: {wf.get('sys_created_on', 'N/A')}\n"
            f"Updated: {wf.get('sys_updated_on', 'N/A')}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def list_ai_agents(
    active_only: bool = True,
    limit: int = 50
) -> str:
    """
    List all AI agents configured in the system.
    
    Args:
        active_only: Only show active agents (default True)
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if active_only:
        query_parts.append("active=true")
    query = "^".join(query_parts) if query_parts else ""
    
    url = f"{INSTANCE}/api/now/table/sn_aia_agent"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on" if query else "ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,name,description,active,agent_role,sys_created_on,sys_updated_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No AI agents found."

    output = []
    for agent in results:
        output.append(
            f"Name: {agent.get('name', 'N/A')}\n"
            f"Sys ID: {agent.get('sys_id')}\n"
            f"Active: {agent.get('active', 'N/A')}\n"
            f"Role: {agent.get('agent_role', 'N/A')}\n"
            f"Description: {agent.get('description', 'N/A')}\n"
            f"Created: {agent.get('sys_created_on', 'N/A')}\n"
            f"Updated: {agent.get('sys_updated_on', 'N/A')}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def get_agent_details(
    agent_name: str = "",
    agent_sys_id: str = ""
) -> str:
    """
    Get detailed information about a specific AI agent including its tools.
    
    Args:
        agent_name: Name of the agent to look up
        agent_sys_id: Sys ID of the agent to look up (more precise than name)
    """
    if not agent_name and not agent_sys_id:
        return "Error: Must provide either agent_name or agent_sys_id"
    
    # First get the agent record
    url = f"{INSTANCE}/api/now/table/sn_aia_agent"
    if agent_sys_id:
        params = {
            "sysparm_query": f"sys_id={agent_sys_id}",
            "sysparm_fields": "sys_id,name,description,active,role,instructions"  # Fixed: use 'role' and 'instructions'
        }
    else:
        params = {
            "sysparm_query": f"nameLIKE{agent_name}",
            "sysparm_limit": 1,
            "sysparm_fields": "sys_id,name,description,active,role,instructions"  # Fixed: use 'role' and 'instructions'
        }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "Agent not found."

    agent = results[0]
    agent_id = agent.get('sys_id')
    
    # Query the agent config table to get active status
    config_url = f"{INSTANCE}/api/now/table/sn_aia_agent_config"
    config_params = {
        "sysparm_query": f"agent={agent_id}",
        "sysparm_fields": "active",
        "sysparm_limit": 1
    }
    
    config_response = requests.get(
        config_url, params=config_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    active_status = "N/A"
    if config_response.status_code == 200:
        config_results = config_response.json().get("result", [])
        if config_results:
            active_status = config_results[0].get('active', 'N/A')
    
    output = [
        f"=== AI AGENT DETAILS ===",
        f"Name: {agent.get('name', 'N/A')}",
        f"Sys ID: {agent_id}",
        f"Active: {active_status}",  # Now gets from config table
        f"Role: {agent.get('role', 'N/A')}",  # Fixed: use 'role' instead of 'agent_role'
        f"Description: {agent.get('description', 'N/A')}",
        f"\nInstructions:\n{agent.get('instructions', 'N/A')}\n"  # Fixed: use 'instructions' instead of 'list_of_steps'
    ]
    
    # Get associated tools
    tool_url = f"{INSTANCE}/api/now/table/sn_aia_agent_tool_m2m"
    tool_params = {
        "sysparm_query": f"agent={agent_id}",
        "sysparm_fields": "tool.name,tool.type,tool.sys_id,max_automatic_executions"
    }
    
    tool_response = requests.get(
        tool_url, params=tool_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if tool_response.status_code == 200:
        tools = tool_response.json().get("result", [])
        if tools:
            output.append("\n=== ASSOCIATED TOOLS ===")
            for tool in tools:
                tool_name = tool.get('tool.name', 'N/A')
                tool_type = tool.get('tool.type', 'N/A')
                max_exec = tool.get('max_automatic_executions', 'N/A')
                output.append(f"- {tool_name} (Type: {tool_type}, Max Auto Executions: {max_exec})")
        else:
            output.append("\n=== ASSOCIATED TOOLS ===\nNo tools configured")
    
    return "\n".join(output)


@mcp.tool()
def list_agent_tools(
    tool_type: str = "",
    limit: int = 50
) -> str:
    """
    List all tools available to AI agents.
    
    Args:
        tool_type: Filter by tool type (flow_action, record_operation, script, etc.)
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if tool_type:
        query_parts.append(f"type={tool_type}")
    query = "^".join(query_parts) if query_parts else ""
    
    url = f"{INSTANCE}/api/now/table/sn_aia_tool"
    params = {
        "sysparm_query": f"{query}^ORDERBYname" if query else "ORDERBYname",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,name,type,description,active"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No tools found."

    output = []
    for tool in results:
        output.append(
            f"Name: {tool.get('name', 'N/A')}\n"
            f"Sys ID: {tool.get('sys_id')}\n"
            f"Type: {tool.get('type', 'N/A')}\n"
            f"Active: {tool.get('active', 'N/A')}\n"
            f"Description: {tool.get('description', 'N/A')}"
        )
    return "\n\n---\n\n".join(output)


# ============================================================================
# AI AGENT EXECUTION & TROUBLESHOOTING TOOLS
# ============================================================================

@mcp.tool()
def query_execution_plans(
    usecase_name: str = "",
    state: str = "",
    minutes_ago: int = 60,
    limit: int = 20
) -> str:
    """
    Query AI agent execution plans (sn_aia_execution_plan).
    Tracks overall agentic workflow runs and high-level plans.
    
    Args:
        usecase_name: Filter by agentic workflow name
        state: Filter by state (complete, in_progress, error, etc.)
        minutes_ago: Only show executions from last N minutes (default 60)
        limit: Max number of records to return (default 20)
    """
    query_parts = []
    if usecase_name:
        query_parts.append(f"usecase.nameLIKE{usecase_name}")
    if state:
        query_parts.append(f"state={state}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sn_aia_execution_plan"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,usecase.name,state,objective,sys_created_on,sys_updated_on,error_message"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No execution plans found matching your criteria."

    output = []
    for plan in results:
        error_msg = plan.get('error_message', '')
        output.append(
            f"Execution ID: {plan.get('sys_id')}\n"
            f"Workflow: {plan.get('usecase.name', 'N/A')}\n"
            f"State: {plan.get('state', 'N/A')}\n"
            f"Objective: {plan.get('objective', 'N/A')}\n"
            f"Created: {plan.get('sys_created_on', 'N/A')}\n"
            f"Updated: {plan.get('sys_updated_on', 'N/A')}"
            + (f"\nError: {error_msg}" if error_msg else "")
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def query_execution_tasks(
    execution_plan_id: str = "",
    agent_name: str = "",
    minutes_ago: int = 60,
    limit: int = 50
) -> str:
    """
    Query AI agent execution tasks (sn_aia_execution_task).
    Tracks individual tool-level tasks within an execution plan.
    
    Args:
        execution_plan_id: Filter by specific execution plan sys_id
        agent_name: Filter by agent name
        minutes_ago: Only show tasks from last N minutes (default 60)
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if execution_plan_id:
        query_parts.append(f"execution_plan={execution_plan_id}")
    if agent_name:
        query_parts.append(f"agent.nameLIKE{agent_name}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sn_aia_execution_task"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,execution_plan,agent.name,state,error_message,sys_created_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No execution tasks found matching your criteria."

    output = []
    for task in results:
        error_msg = task.get('error_message', '')
        output.append(
            f"Task ID: {task.get('sys_id')}\n"
            f"Execution Plan: {task.get('execution_plan', 'N/A')}\n"
            f"Agent: {task.get('agent.name', 'N/A')}\n"
            f"State: {task.get('state', 'N/A')}\n"
            f"Created: {task.get('sys_created_on', 'N/A')}"
            + (f"\nError: {error_msg}" if error_msg else "")
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def query_tool_executions(
    execution_plan_id: str = "",
    tool_name: str = "",
    minutes_ago: int = 60,
    limit: int = 20
) -> str:
    """
    Query tool executions to see which tools were called and their results.
    
    Args:
        execution_plan_id: Filter by specific execution plan sys_id
        tool_name: Filter by tool name
        minutes_ago: Only show executions from last N minutes (default 60)
        limit: Max number of records to return (default 20)
    """
    query_parts = []
    if execution_plan_id:
        query_parts.append(f"execution_plan={execution_plan_id}")
    if tool_name:
        query_parts.append(f"tool.nameLIKE{tool_name}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sn_aia_tools_execution"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,tool.name,agent.name,state,error_message,sys_created_on,output"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No tool executions found matching your criteria."

    output = []
    for tool_exec in results:
        error_msg = tool_exec.get('error_message', '')
        tool_output = tool_exec.get('output', '')
        output.append(
            f"Tool: {tool_exec.get('tool.name', 'N/A')}\n"
            f"Agent: {tool_exec.get('agent.name', 'N/A')}\n"
            f"State: {tool_exec.get('state', 'N/A')}\n"
            f"Created: {tool_exec.get('sys_created_on', 'N/A')}"
            + (f"\nError: {error_msg}" if error_msg else "")
            + (f"\nOutput (first 500 chars): {tool_output[:500]}" if tool_output else "")
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def get_execution_details(
    execution_plan_id: str
) -> str:
    """
    Get complete details of an agentic workflow execution including all tasks and tool calls.
    
    Args:
        execution_plan_id: Sys ID of the execution plan to investigate
    """
    # Get execution plan
    plan_url = f"{INSTANCE}/api/now/table/sn_aia_execution_plan/{execution_plan_id}"
    params = {
        "sysparm_fields": "sys_id,usecase.name,agent.name,state,objective,error_message,sys_created_on,sys_updated_on"
    }

    plan_response = requests.get(
        plan_url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if plan_response.status_code != 200:
        return f"Error: {plan_response.status_code} - {plan_response.text}"

    plan = plan_response.json().get("result", {})
    if not plan:
        return "Execution plan not found."

    output = [
        "=== EXECUTION PLAN DETAILS ===",
        f"Execution ID: {plan.get('sys_id')}",
        f"Workflow: {plan.get('usecase.name', 'N/A')}",
        f"Primary Agent: {plan.get('agent.name', 'N/A')}",
        f"State: {plan.get('state', 'N/A')}",
        f"Objective: {plan.get('objective', 'N/A')}",
        f"Created: {plan.get('sys_created_on', 'N/A')}",
        f"Updated: {plan.get('sys_updated_on', 'N/A')}"
    ]
    
    error_msg = plan.get('error_message', '')
    if error_msg:
        output.append(f"\n=== ERROR MESSAGE ===\n{error_msg}")

    # Get execution tasks
    task_url = f"{INSTANCE}/api/now/table/sn_aia_execution_task"
    task_params = {
        "sysparm_query": f"execution_plan={execution_plan_id}^ORDERBYsys_created_on",
        "sysparm_fields": "agent.name,state,sys_created_on"
    }

    task_response = requests.get(
        task_url, params=task_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if task_response.status_code == 200:
        tasks = task_response.json().get("result", [])
        if tasks:
            output.append("\n=== EXECUTION TASKS ===")
            for i, task in enumerate(tasks, 1):
                output.append(
                    f"{i}. Agent: {task.get('agent.name', 'N/A')} | "
                    f"State: {task.get('state', 'N/A')} | "
                    f"Time: {task.get('sys_created_on', 'N/A')}"
                )

    # Get tool executions
    tool_url = f"{INSTANCE}/api/now/table/sn_aia_tools_execution"
    tool_params = {
        "sysparm_query": f"execution_plan={execution_plan_id}^ORDERBYsys_created_on",
        "sysparm_fields": "tool.name,agent.name,state,error_message,sys_created_on"
    }

    tool_response = requests.get(
        tool_url, params=tool_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if tool_response.status_code == 200:
        tools = tool_response.json().get("result", [])
        if tools:
            output.append("\n=== TOOL EXECUTIONS ===")
            for i, tool_exec in enumerate(tools, 1):
                error = tool_exec.get('error_message', '')
                output.append(
                    f"{i}. Tool: {tool_exec.get('tool.name', 'N/A')} | "
                    f"Agent: {tool_exec.get('agent.name', 'N/A')} | "
                    f"State: {tool_exec.get('state', 'N/A')}"
                    + (f"\n   Error: {error}" if error else "")
                )

    return "\n".join(output)


@mcp.tool()
def query_generative_ai_logs(
    minutes_ago: int = 60,
    limit: int = 20
) -> str:
    """
    Query generative AI logs (sys_generative_ai_log).
    Central log for tracking AI Agent invocations and LLM interactions.
    
    Args:
        minutes_ago: Only show logs from last N minutes (default 60)
        limit: Max number of records to return (default 20)
    """
    query = f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}"

    url = f"{INSTANCE}/api/now/table/sys_generative_ai_log"
    params = {
        "sysparm_query": f"{query}^ORDERBYDESCsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,capability,model,status,error_message,sys_created_on,token_count"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No generative AI logs found."

    output = []
    for log in results:
        error_msg = log.get('error_message', '')
        output.append(
            f"Capability: {log.get('capability', 'N/A')}\n"
            f"Model: {log.get('model', 'N/A')}\n"
            f"Status: {log.get('status', 'N/A')}\n"
            f"Tokens: {log.get('token_count', 'N/A')}\n"
            f"Created: {log.get('sys_created_on', 'N/A')}"
            + (f"\nError: {error_msg}" if error_msg else "")
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def query_agent_messages(
    execution_plan_id: str = "",
    minutes_ago: int = 60,
    limit: int = 50
) -> str:
    """
    Query AI agent conversation messages (sn_aia_message).
    Stores conversation data including tool outputs and short-term memory.
    
    Args:
        execution_plan_id: Filter by specific execution plan sys_id
        minutes_ago: Only show messages from last N minutes (default 60)
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if execution_plan_id:
        query_parts.append(f"execution_plan={execution_plan_id}")
    query_parts.append(f"sys_created_onRELATIVEGT@minute@ago@{minutes_ago}")
    query = "^".join(query_parts)

    url = f"{INSTANCE}/api/now/table/sn_aia_message"
    params = {
        "sysparm_query": f"{query}^ORDERBYsys_created_on",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,execution_plan,role,content,sys_created_on"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No agent messages found matching your criteria."

    output = []
    for msg in results:
        content = msg.get('content', '')
        output.append(
            f"[{msg.get('sys_created_on')}] {msg.get('role', 'N/A').upper()}\n"
            f"Execution Plan: {msg.get('execution_plan', 'N/A')}\n"
            f"Content (first 500 chars): {content[:500]}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def list_trigger_configurations(
    usecase_name: str = "",
    limit: int = 50
) -> str:
    """
    List trigger configurations for agentic workflows.
    
    Args:
        usecase_name: Filter by agentic workflow name
        limit: Max number of records to return (default 50)
    """
    query_parts = []
    if usecase_name:
        query_parts.append(f"usecase.nameLIKE{usecase_name}")
    query = "^".join(query_parts) if query_parts else ""
    
    url = f"{INSTANCE}/api/now/table/sn_aia_trigger_configuration"
    params = {
        "sysparm_query": f"{query}^ORDERBYusecase.name" if query else "ORDERBYusecase.name",
        "sysparm_limit": limit,
        "sysparm_fields": "sys_id,usecase.name,trigger_type,table,condition,active"
    }

    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    results = response.json().get("result", [])
    if not results:
        return "No trigger configurations found."

    output = []
    for trigger in results:
        output.append(
            f"Workflow: {trigger.get('usecase.name', 'N/A')}\n"
            f"Trigger Type: {trigger.get('trigger_type', 'N/A')}\n"
            f"Table: {trigger.get('table', 'N/A')}\n"
            f"Condition: {trigger.get('condition', 'N/A')}\n"
            f"Active: {trigger.get('active', 'N/A')}"
        )
    return "\n\n---\n\n".join(output)


# ============================================================================
# AI AGENT WRITE OPERATIONS
# ============================================================================

@mcp.tool()
def create_ai_agent(
    name: str,
    description: str,
    agent_role: str,
    list_of_steps: str,
    active: bool = True
) -> str:
    """
    Create a new AI agent.
    
    Args:
        name: Name of the agent (e.g., "Custom Incident Resolver")
        description: Brief description of what the agent does
        agent_role: The agent's role/purpose (e.g., "Incident resolution specialist")
        list_of_steps: Detailed step-by-step instructions for the agent
        active: Whether the agent is active (default True)
    
    Returns:
        Success message with agent sys_id
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_agent"
    
    payload = {
        "name": name,
        "description": description,
        "role": agent_role,  # Fixed: use 'role' instead of 'agent_role'
        "instructions": list_of_steps,  # Fixed: use 'instructions' instead of 'list_of_steps'
        "active": str(active).lower()
    }
    
    response = requests.post(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json().get("result", {})
        agent_id = result.get("sys_id")
        
        # Update the auto-created agent config record to set active status
        # ServiceNow creates this automatically, we just need to update it
        config_url = f"{INSTANCE}/api/now/table/sn_aia_agent_config"
        config_params = {
            "sysparm_query": f"agent={agent_id}",
            "sysparm_fields": "sys_id",
            "sysparm_limit": 1
        }
        
        config_get_response = requests.get(
            config_url,
            params=config_params,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"}
        )
        
        config_updated = False
        if config_get_response.status_code == 200:
            config_results = config_get_response.json().get("result", [])
            if config_results:
                # Update existing config
                config_id = config_results[0].get("sys_id")
                config_update_url = f"{INSTANCE}/api/now/table/sn_aia_agent_config/{config_id}"
                config_payload = {"active": str(active).lower()}
                
                config_update_response = requests.patch(
                    config_update_url,
                    json=config_payload,
                    auth=(USERNAME, PASSWORD),
                    headers={"Accept": "application/json", "Content-Type": "application/json"}
                )
                
                config_updated = config_update_response.status_code == 200
        
        return (
            f"âœ… AI Agent created successfully!\n\n"
            f"Name: {name}\n"
            f"Sys ID: {agent_id}\n"
            f"Active: {active}"
            + (f" (config updated)" if config_updated else f" (auto-created)")
            + f"\n\nNext steps:\n"
            f"1. Add tools to the agent using add_tool_to_agent\n"
            f"2. Associate with workflows using create_agentic_workflow or update_agentic_workflow\n"
            f"3. Test the agent in AI Agent Studio"
        )
    else:
        return f"âŒ Error creating agent: {response.status_code} - {response.text}"


@mcp.tool()
def update_ai_agent(
    agent_sys_id: str,
    name: str = "",
    description: str = "",
    agent_role: str = "",
    list_of_steps: str = "",
    active: str = ""
) -> str:
    """
    Update an existing AI agent. Only provide fields you want to update.
    
    Args:
        agent_sys_id: Sys ID of the agent to update (required)
        name: New name (optional)
        description: New description (optional)
        agent_role: New role (optional)
        list_of_steps: New instructions (optional)
        active: New active status - "true" or "false" (optional)
    
    Returns:
        Success message with updated fields
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_agent/{agent_sys_id}"
    
    # Separate active from other fields since it goes in a different table
    active_value = None
    if active:
        active_value = active
        # Don't include active in the main agent payload
    
    # Only include fields that were provided (excluding active)
    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if agent_role:
        payload["role"] = agent_role  # Fixed: use 'role' instead of 'agent_role'
    if list_of_steps:
        payload["instructions"] = list_of_steps  # Fixed: use 'instructions' instead of 'list_of_steps'
    
    updated_fields = []
    
    # Update the main agent record if there are fields to update
    if payload:
        response = requests.patch(
            url,
            json=payload,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return f"âŒ Error updating agent: {response.status_code} - {response.text}"
        
        updated_fields = list(payload.keys())
    
    # Update active status in config table if provided
    if active_value:
        # Find the config record
        config_url = f"{INSTANCE}/api/now/table/sn_aia_agent_config"
        config_params = {
            "sysparm_query": f"agent={agent_sys_id}",
            "sysparm_limit": 1,
            "sysparm_fields": "sys_id"
        }
        
        config_response = requests.get(
            config_url, params=config_params,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"}
        )
        
        if config_response.status_code == 200:
            config_results = config_response.json().get("result", [])
            if config_results:
                # Update existing config
                config_id = config_results[0].get("sys_id")
                config_update_url = f"{INSTANCE}/api/now/table/sn_aia_agent_config/{config_id}"
                config_payload = {"active": active_value.lower()}
                
                config_update = requests.patch(
                    config_update_url,
                    json=config_payload,
                    auth=(USERNAME, PASSWORD),
                    headers={"Accept": "application/json", "Content-Type": "application/json"}
                )
                
                if config_update.status_code == 200:
                    updated_fields.append("active (in config)")
            else:
                # Create new config if it doesn't exist
                config_create_payload = {
                    "agent": agent_sys_id,
                    "active": active_value.lower()
                }
                
                config_create = requests.post(
                    config_url,
                    json=config_create_payload,
                    auth=(USERNAME, PASSWORD),
                    headers={"Accept": "application/json", "Content-Type": "application/json"}
                )
                
                if config_create.status_code in [200, 201]:
                    updated_fields.append("active (config created)")
    
    if not updated_fields:
        return "âŒ Error: No fields provided to update. Specify at least one field to change."
    
    return (
        f"âœ… AI Agent updated successfully!\n\n"
        f"Agent ID: {agent_sys_id}\n"
        f"Updated fields: {', '.join(updated_fields)}\n\n"
        f"Use get_agent_details to see the updated configuration."
    )


@mcp.tool()
def delete_ai_agent(
    agent_sys_id: str,
    confirm: bool = False
) -> str:
    """
    Delete an AI agent. Requires confirmation.
    
    Args:
        agent_sys_id: Sys ID of the agent to delete
        confirm: Must be True to proceed with deletion
    
    Returns:
        Success or error message
    """
    if not confirm:
        return (
            f"âš ï¸  Deletion requires confirmation.\n\n"
            f"To delete agent {agent_sys_id}, call this tool again with confirm=True.\n\n"
            f"WARNING: This will remove the agent and its tool associations."
        )
    
    url = f"{INSTANCE}/api/now/table/sn_aia_agent/{agent_sys_id}"
    
    response = requests.delete(
        url,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 204:
        return f"âœ… AI Agent {agent_sys_id} deleted successfully."
    else:
        return f"âŒ Error deleting agent: {response.status_code} - {response.text}"


@mcp.tool()
def add_tool_to_agent(
    agent_sys_id: str,
    tool_sys_id: str,
    max_automatic_executions: int = 5,
    inputs: str = ""
) -> str:
    """
    Add a tool to an AI agent with optional input definitions.
    
    Args:
        agent_sys_id: Sys ID of the agent
        tool_sys_id: Sys ID of the tool to add
        max_automatic_executions: Max times tool can auto-execute (default 5)
        inputs: JSON string defining tool inputs. Format: [{"name":"param1","description":"Param description","mandatory":true}]
    
    Returns:
        Success message
    
    Example with inputs:
        inputs='[{"name":"incident_number","description":"The incident number to look up","mandatory":true}]'
    """
    import json
    
    # First, get the tool name to populate the required name field
    tool_url = f"{INSTANCE}/api/now/table/sn_aia_tool/{tool_sys_id}"
    tool_params = {"sysparm_fields": "name"}
    
    tool_response = requests.get(
        tool_url,
        params=tool_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if tool_response.status_code != 200:
        return f"âŒ Error retrieving tool details: {tool_response.status_code} - {tool_response.text}"
    
    tool_data = tool_response.json().get("result", {})
    tool_name = tool_data.get("name", "Unknown Tool")
    
    # Now create the agent-tool relationship
    url = f"{INSTANCE}/api/now/table/sn_aia_agent_tool_m2m"
    
    payload = {
        "agent": agent_sys_id,
        "tool": tool_sys_id,
        "name": f"Agent Tool: {tool_name}",  # Required field
        "max_automatic_executions": max_automatic_executions
    }
    
    # Add inputs if provided
    if inputs:
        try:
            # Parse the input JSON
            input_list = json.loads(inputs)
            
            # Transform to ServiceNow format with all required fields
            formatted_inputs = []
            for inp in input_list:
                formatted_inputs.append({
                    "name": inp.get("name", ""),
                    "value": inp.get("value", ""),
                    "description": inp.get("description", ""),
                    "mandatory": inp.get("mandatory", False),
                    "invalidMessage": inp.get("invalidMessage", None)
                })
            
            # Set the inputs field as JSON string
            payload["inputs"] = json.dumps(formatted_inputs)
            
        except json.JSONDecodeError as e:
            return f"âŒ Error parsing inputs JSON: {str(e)}"
    
    response = requests.post(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json().get("result", {})
        inputs_count = len(json.loads(inputs)) if inputs else 0
        inputs_info = f"\nInputs Configured: {inputs_count}" if inputs else ""
        return (
            f"âœ… Tool added to agent successfully!\n\n"
            f"Agent: {agent_sys_id}\n"
            f"Tool: {tool_name} ({tool_sys_id})\n"
            f"Max Auto Executions: {max_automatic_executions}"
            f"{inputs_info}\n\n"
            f"Use get_agent_details to see all configured tools."
        )
    else:
        return f"âŒ Error adding tool to agent: {response.status_code} - {response.text}"


@mcp.tool()
def remove_tool_from_agent(
    agent_sys_id: str,
    tool_sys_id: str
) -> str:
    """
    Remove a tool from an AI agent.
    
    Args:
        agent_sys_id: Sys ID of the agent
        tool_sys_id: Sys ID of the tool to remove
    
    Returns:
        Success message
    """
    # First find the m2m record
    url = f"{INSTANCE}/api/now/table/sn_aia_agent_tool_m2m"
    params = {
        "sysparm_query": f"agent={agent_sys_id}^tool={tool_sys_id}",
        "sysparm_fields": "sys_id"
    }
    
    response = requests.get(
        url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code != 200:
        return f"âŒ Error finding tool association: {response.status_code} - {response.text}"
    
    results = response.json().get("result", [])
    if not results:
        return f"âŒ No association found between agent {agent_sys_id} and tool {tool_sys_id}"
    
    m2m_id = results[0].get("sys_id")
    
    # Delete the m2m record
    delete_url = f"{INSTANCE}/api/now/table/sn_aia_agent_tool_m2m/{m2m_id}"
    delete_response = requests.delete(
        delete_url,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if delete_response.status_code == 204:
        return (
            f"âœ… Tool removed from agent successfully!\n\n"
            f"Agent: {agent_sys_id}\n"
            f"Tool: {tool_sys_id}"
        )
    else:
        return f"âŒ Error removing tool: {delete_response.status_code} - {delete_response.text}"


# ============================================================================
# AGENTIC WORKFLOW WRITE OPERATIONS
# ============================================================================

@mcp.tool()
def create_agentic_workflow(
    name: str,
    description: str,
    list_of_steps: str,
    active: bool = True
) -> str:
    """
    Create a new agentic workflow (use case).
    
    Args:
        name: Name of the workflow (e.g., "Custom Incident Investigation")
        description: Brief description of what the workflow does
        list_of_steps: Detailed step-by-step instructions for the workflow
        active: Whether the workflow is active (default True)
    
    Returns:
        Success message with workflow sys_id
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_usecase"
    
    payload = {
        "name": name,
        "description": description,
        "list_of_steps": list_of_steps,
        "active": str(active).lower()
    }
    
    response = requests.post(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json().get("result", {})
        workflow_id = result.get("sys_id")
        return (
            f"âœ… Agentic Workflow created successfully!\n\n"
            f"Name: {name}\n"
            f"Sys ID: {workflow_id}\n"
            f"Active: {active}\n\n"
            f"Next steps:\n"
            f"1. Associate agents with this workflow\n"
            f"2. Create triggers using create_trigger\n"
            f"3. Test the workflow in AI Agent Studio"
        )
    else:
        return f"âŒ Error creating workflow: {response.status_code} - {response.text}"


@mcp.tool()
def update_agentic_workflow(
    workflow_sys_id: str,
    name: str = "",
    description: str = "",
    list_of_steps: str = "",
    active: str = ""
) -> str:
    """
    Update an existing agentic workflow. Only provide fields you want to update.
    
    Args:
        workflow_sys_id: Sys ID of the workflow to update (required)
        name: New name (optional)
        description: New description (optional)
        list_of_steps: New instructions (optional)
        active: New active status - "true" or "false" (optional)
    
    Returns:
        Success message with updated fields
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_usecase/{workflow_sys_id}"
    
    # Only include fields that were provided
    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if list_of_steps:
        payload["list_of_steps"] = list_of_steps
    if active:
        payload["active"] = active.lower()
    
    if not payload:
        return "âŒ Error: No fields provided to update. Specify at least one field to change."
    
    response = requests.patch(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        updated_fields = ", ".join(payload.keys())
        return (
            f"âœ… Agentic Workflow updated successfully!\n\n"
            f"Workflow ID: {workflow_sys_id}\n"
            f"Updated fields: {updated_fields}"
        )
    else:
        return f"âŒ Error updating workflow: {response.status_code} - {response.text}"


@mcp.tool()
def delete_agentic_workflow(
    workflow_sys_id: str,
    confirm: bool = False
) -> str:
    """
    Delete an agentic workflow. Requires confirmation.
    
    Args:
        workflow_sys_id: Sys ID of the workflow to delete
        confirm: Must be True to proceed with deletion
    
    Returns:
        Success or error message
    """
    if not confirm:
        return (
            f"âš ï¸  Deletion requires confirmation.\n\n"
            f"To delete workflow {workflow_sys_id}, call this tool again with confirm=True.\n\n"
            f"WARNING: This will remove the workflow and its triggers."
        )
    
    url = f"{INSTANCE}/api/now/table/sn_aia_usecase/{workflow_sys_id}"
    
    response = requests.delete(
        url,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 204:
        return f"âœ… Agentic Workflow {workflow_sys_id} deleted successfully."
    else:
        return f"âŒ Error deleting workflow: {response.status_code} - {response.text}"


# ============================================================================
# TOOL WRITE OPERATIONS
# ============================================================================

@mcp.tool()
def create_tool(
    name: str,
    description: str,
    tool_type: str,
    active: bool = True,
    flow_action_sys_id: str = "",
    script_content: str = ""
) -> str:
    """
    Create a new tool for AI agents.
    
    Args:
        name: Name of the tool (e.g., "Fetch Incident Details")
        description: What the tool does
        tool_type: Type of tool (flow_action, record_operation, script, search_retrieval, etc.)
        active: Whether the tool is active (default True)
        flow_action_sys_id: If type is flow_action, the sys_id of the flow action
        script_content: If type is script, the script code
    
    Returns:
        Success message with tool sys_id
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_tool"
    
    payload = {
        "name": name,
        "description": description,
        "type": tool_type,
        "active": str(active).lower()
    }
    
    # Add type-specific fields
    if tool_type == "flow_action" and flow_action_sys_id:
        payload["flow_action"] = flow_action_sys_id
    elif tool_type == "script" and script_content:
        payload["script"] = script_content
    
    response = requests.post(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json().get("result", {})
        tool_id = result.get("sys_id")
        return (
            f"âœ… Tool created successfully!\n\n"
            f"Name: {name}\n"
            f"Type: {tool_type}\n"
            f"Sys ID: {tool_id}\n"
            f"Active: {active}\n\n"
            f"Next step: Use add_tool_to_agent to associate this tool with agents."
        )
    else:
        return f"âŒ Error creating tool: {response.status_code} - {response.text}"


@mcp.tool()
def update_tool(
    tool_sys_id: str,
    name: str = "",
    description: str = "",
    active: str = "",
    script_content: str = ""
) -> str:
    """
    Update an existing tool. Only provide fields you want to update.
    
    Args:
        tool_sys_id: Sys ID of the tool to update (required)
        name: New name (optional)
        description: New description (optional)
        active: New active status - "true" or "false" (optional)
        script_content: New script content if type is script (optional)
    
    Returns:
        Success message with updated fields
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_tool/{tool_sys_id}"
    
    # Only include fields that were provided
    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if active:
        payload["active"] = active.lower()
    if script_content:
        payload["script"] = script_content
    
    if not payload:
        return "âŒ Error: No fields provided to update. Specify at least one field to change."
    
    response = requests.patch(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        updated_fields = ", ".join(payload.keys())
        return (
            f"âœ… Tool updated successfully!\n\n"
            f"Tool ID: {tool_sys_id}\n"
            f"Updated fields: {updated_fields}"
        )
    else:
        return f"âŒ Error updating tool: {response.status_code} - {response.text}"


@mcp.tool()
def delete_tool(
    tool_sys_id: str,
    confirm: bool = False
) -> str:
    """
    Delete a tool. Requires confirmation.
    
    Args:
        tool_sys_id: Sys ID of the tool to delete
        confirm: Must be True to proceed with deletion
    
    Returns:
        Success or error message
    """
    if not confirm:
        return (
            f"âš ï¸  Deletion requires confirmation.\n\n"
            f"To delete tool {tool_sys_id}, call this tool again with confirm=True.\n\n"
            f"WARNING: This will remove the tool from all agents using it."
        )
    
    url = f"{INSTANCE}/api/now/table/sn_aia_tool/{tool_sys_id}"
    
    response = requests.delete(
        url,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 204:
        return f"âœ… Tool {tool_sys_id} deleted successfully."
    else:
        return f"âŒ Error deleting tool: {response.status_code} - {response.text}"


# ============================================================================
# TRIGGER WRITE OPERATIONS
# ============================================================================

@mcp.tool()
def create_trigger(
    workflow_sys_id: str,
    trigger_type: str,
    table: str = "",
    condition: str = "",
    active: bool = True
) -> str:
    """
    Create a trigger for an agentic workflow.
    
    Args:
        workflow_sys_id: Sys ID of the workflow this trigger starts
        trigger_type: Type of trigger (on_demand, record_created, record_updated, etc.)
        table: Table name if record-based trigger (e.g., "incident")
        condition: Encoded query condition (e.g., "priority=1^state=1")
        active: Whether the trigger is active (default True)
    
    Returns:
        Success message with trigger sys_id
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_trigger_configuration"
    
    payload = {
        "usecase": workflow_sys_id,
        "trigger_type": trigger_type,
        "active": str(active).lower()
    }
    
    # Add optional fields
    if table:
        payload["table"] = table
    if condition:
        payload["condition"] = condition
    
    response = requests.post(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json().get("result", {})
        trigger_id = result.get("sys_id")
        return (
            f"âœ… Trigger created successfully!\n\n"
            f"Trigger ID: {trigger_id}\n"
            f"Workflow: {workflow_sys_id}\n"
            f"Type: {trigger_type}\n"
            f"Table: {table if table else 'N/A'}\n"
            f"Active: {active}\n\n"
            f"The workflow will now execute when this trigger fires."
        )
    else:
        return f"âŒ Error creating trigger: {response.status_code} - {response.text}"


@mcp.tool()
def update_trigger(
    trigger_sys_id: str,
    trigger_type: str = "",
    table: str = "",
    condition: str = "",
    active: str = ""
) -> str:
    """
    Update an existing trigger. Only provide fields you want to update.
    
    Args:
        trigger_sys_id: Sys ID of the trigger to update (required)
        trigger_type: New trigger type (optional)
        table: New table (optional)
        condition: New condition (optional)
        active: New active status - "true" or "false" (optional)
    
    Returns:
        Success message with updated fields
    """
    url = f"{INSTANCE}/api/now/table/sn_aia_trigger_configuration/{trigger_sys_id}"
    
    # Only include fields that were provided
    payload = {}
    if trigger_type:
        payload["trigger_type"] = trigger_type
    if table:
        payload["table"] = table
    if condition:
        payload["condition"] = condition
    if active:
        payload["active"] = active.lower()
    
    if not payload:
        return "âŒ Error: No fields provided to update. Specify at least one field to change."
    
    response = requests.patch(
        url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        updated_fields = ", ".join(payload.keys())
        return (
            f"âœ… Trigger updated successfully!\n\n"
            f"Trigger ID: {trigger_sys_id}\n"
            f"Updated fields: {updated_fields}"
        )
    else:
        return f"âŒ Error updating trigger: {response.status_code} - {response.text}"


@mcp.tool()
def delete_trigger(
    trigger_sys_id: str,
    confirm: bool = False
) -> str:
    """
    Delete a trigger. Requires confirmation.
    
    Args:
        trigger_sys_id: Sys ID of the trigger to delete
        confirm: Must be True to proceed with deletion
    
    Returns:
        Success or error message
    """
    if not confirm:
        return (
            f"âš ï¸  Deletion requires confirmation.\n\n"
            f"To delete trigger {trigger_sys_id}, call this tool again with confirm=True."
        )
    
    url = f"{INSTANCE}/api/now/table/sn_aia_trigger_configuration/{trigger_sys_id}"
    
    response = requests.delete(
        url,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 204:
        return f"âœ… Trigger {trigger_sys_id} deleted successfully."
    else:
        return f"âŒ Error deleting trigger: {response.status_code} - {response.text}"


# ============================================================================
# HELPER/UTILITY OPERATIONS
# ============================================================================

@mcp.tool()
def clone_ai_agent(
    source_agent_sys_id: str,
    new_name: str,
    new_description: str = ""
) -> str:
    """
    Clone an existing AI agent with all its tools and configuration.
    
    Args:
        source_agent_sys_id: Sys ID of the agent to clone
        new_name: Name for the new agent
        new_description: Description for the new agent (optional, uses source if not provided)
    
    Returns:
        Success message with new agent sys_id
    """
    # Get the source agent
    source_url = f"{INSTANCE}/api/now/table/sn_aia_agent/{source_agent_sys_id}"
    params = {
        "sysparm_fields": "name,description,agent_role,list_of_steps,active"
    }
    
    source_response = requests.get(
        source_url, params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if source_response.status_code != 200:
        return f"âŒ Error retrieving source agent: {source_response.status_code} - {source_response.text}"
    
    source = source_response.json().get("result", {})
    if not source:
        return f"âŒ Source agent {source_agent_sys_id} not found."
    
    # Create new agent with source configuration
    create_url = f"{INSTANCE}/api/now/table/sn_aia_agent"
    payload = {
        "name": new_name,
        "description": new_description if new_description else source.get("description", ""),
        "agent_role": source.get("agent_role", ""),
        "list_of_steps": source.get("list_of_steps", ""),
        "active": source.get("active", "true")
    }
    
    create_response = requests.post(
        create_url,
        json=payload,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    
    if create_response.status_code not in [200, 201]:
        return f"âŒ Error creating cloned agent: {create_response.status_code} - {create_response.text}"
    
    new_agent = create_response.json().get("result", {})
    new_agent_id = new_agent.get("sys_id")
    
    # Get source agent's tools with their inputs
    tools_url = f"{INSTANCE}/api/now/table/sn_aia_agent_tool_m2m"
    tools_params = {
        "sysparm_query": f"agent={source_agent_sys_id}",
        "sysparm_fields": "tool,max_automatic_executions,inputs"  # Include inputs field
    }
    
    tools_response = requests.get(
        tools_url, params=tools_params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    tools_cloned = 0
    if tools_response.status_code == 200:
        tools = tools_response.json().get("result", [])
        for tool in tools:
            # Get the tool sys_id reference value
            tool_ref = tool.get("tool")
            
            # Extract sys_id from reference if it's a dict
            if isinstance(tool_ref, dict):
                tool_sys_id = tool_ref.get("value")
            else:
                tool_sys_id = tool_ref
            
            # Get tool name for the required name field
            tool_name_response = requests.get(
                f"{INSTANCE}/api/now/table/sn_aia_tool/{tool_sys_id}",
                params={"sysparm_fields": "name"},
                auth=(USERNAME, PASSWORD),
                headers={"Accept": "application/json"}
            )
            
            tool_name = "Tool"
            if tool_name_response.status_code == 200:
                tool_name = tool_name_response.json().get("result", {}).get("name", "Tool")
            
            tool_payload = {
                "agent": new_agent_id,
                "tool": tool_sys_id,
                "name": f"Agent Tool: {tool_name}",  # Required field
                "max_automatic_executions": tool.get("max_automatic_executions", 5)
            }
            
            # Include inputs if they exist in the source
            if tool.get("inputs"):
                tool_payload["inputs"] = tool.get("inputs")
            
            tool_create_response = requests.post(
                f"{INSTANCE}/api/now/table/sn_aia_agent_tool_m2m",
                json=tool_payload,
                auth=(USERNAME, PASSWORD),
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
            
            if tool_create_response.status_code in [200, 201]:
                tools_cloned += 1
    
    return (
        f"âœ… AI Agent cloned successfully!\n\n"
        f"Source Agent: {source.get('name')}\n"
        f"New Agent: {new_name}\n"
        f"New Agent ID: {new_agent_id}\n"
        f"Tools Cloned: {tools_cloned}\n\n"
        f"The new agent has the same configuration and tools as the source."
    )


if __name__ == "__main__":
    mcp.run()
# Function to add to server.py for cleaning up duplicate agent configs

@mcp.tool()
def cleanup_agent_configs(
    agent_sys_id: str
) -> str:
    """
    Clean up duplicate agent config records for an agent.
    Keeps the most recent config record and deletes older duplicates.
    
    Args:
        agent_sys_id: Sys ID of the agent to clean up configs for
    
    Returns:
        Success message with cleanup details
    """
    # Query all config records for this agent
    url = f"{INSTANCE}/api/now/table/sn_aia_agent_config"
    params = {
        "sysparm_query": f"agent={agent_sys_id}^ORDERBYDESCsys_created_on",
        "sysparm_fields": "sys_id,active,sys_created_on"
    }
    
    response = requests.get(
        url,
        params=params,
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code != 200:
        return f"âŒ Error querying configs: {response.status_code} - {response.text}"
    
    configs = response.json().get("result", [])
    
    if len(configs) <= 1:
        return f"âœ… No cleanup needed. Agent has {len(configs)} config record(s)."
    
    # Keep the first one (most recent), delete the rest
    kept_config = configs[0]
    deleted_count = 0
    
    for config in configs[1:]:
        delete_url = f"{INSTANCE}/api/now/table/sn_aia_agent_config/{config.get('sys_id')}"
        delete_response = requests.delete(
            delete_url,
            auth=(USERNAME, PASSWORD),
            headers={"Accept": "application/json"}
        )
        
        if delete_response.status_code == 204:
            deleted_count += 1
    
    return (
        f"âœ… Agent config cleanup completed!\n\n"
        f"Agent: {agent_sys_id}\n"
        f"Total configs found: {len(configs)}\n"
        f"Configs deleted: {deleted_count}\n"
        f"Active config kept: {kept_config.get('sys_id')} (Active: {kept_config.get('active')})"
    )
