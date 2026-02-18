# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-18

### Added
- Initial public release
- **40+ MCP tools** across five categories:
  - Debugging: `query_syslog`, `query_generative_ai_logs`, `query_generative_ai_logs_detailed`
  - Flow Designer: `query_flow_contexts`, `query_flow_logs`, `get_flow_context_details`, `query_flow_reports`
  - AI Agent Config: `list_ai_agents`, `list_agentic_workflows`, `get_agent_details`, `list_agent_tools`, `list_trigger_configurations`
  - Execution Monitoring: `query_execution_plans`, `query_execution_tasks`, `query_tool_executions`, `get_execution_details`, `query_agent_messages`
  - Write Operations: Full CRUD for agents, workflows, tools, and triggers
  - Utilities: `clone_ai_agent`, `cleanup_agent_configs`
- Validation and test suite: `quick_validation.py`, `test_connection.py`, `test_detailed.py`, `test_mcp_server.py`
- macOS and Windows setup support
- Apache 2.0 license
