# MCP Integration with ADK Web

## Overview

The agent has been updated to use MCP tools via `MCPToolset` with stdio communication. The ADK runner now automatically spawns and manages the MCP server as a subprocess when you run `adk web`.

## How It Works

1. **adk web**: The web-based UI you use to interact with the agent
2. **adk runner**: The engine that runs your agent and manages the MCP server lifecycle
3. **MCP server**: The DataGolf server that provides tools to fetch player data

When you start `adk web`, the runner:
- Reads the MCPToolset configuration in `agent.py`
- Automatically spawns `mcp_servers/datagolf_server.py` as a subprocess
- Communicates with it via stdio (standard input/output)
- Discovers and makes available the `getPlayerTrueStrokesGained` tool
- Automatically stops the server when the agent terminates

## Files Modified

### 1. `ryder_cup_prediction/agent.py`
- Added imports for `MCPToolset`, `StdioConnectionParams`, and `StdioServerParameters`
- Configured `MCPToolset` to spawn the MCP server automatically:
  ```python
  mcp_server_config = StdioServerParameters(
      command=sys.executable,  # Current Python interpreter
      args=[mcp_script_path]   # Path to datagolf_server.py
  )
  
  mcp_connection_config = StdioConnectionParams(
      server_params=mcp_server_config,
      timeout=10
  )
  
  managed_mcp_tools = MCPToolset(
      connection_params=mcp_connection_config
  )
  ```
- The toolset is passed to `get_sub_agents()` which makes it available to PlayerProfilerAgent

### 2. `ryder_cup_prediction/__init__.py`
- Exposed `root_agent` to make it discoverable by `adk web`

### 3. `mcp_servers/datagolf_server.py`
- Added logging configuration (logs to `mcp_server.log`)
- Enhanced error handling in the `main()` function
- Added log statements for debugging tool calls

## Project Structure

```
rydercup_predictor_agent_copilot/
├── mcp_servers/
│   ├── __init__.py
│   └── datagolf_server.py       # MCP server (spawned as subprocess)
├── ryder_cup_prediction/
│   ├── __init__.py               # Exposes root_agent
│   ├── agent.py                  # Configures MCPToolset
│   └── sub_agent_definitions.py
├── pyproject.toml
└── run_prediction.py
```

## Running the Agent

Simply run:
```bash
uv run adk web
```

The ADK runner will:
1. Load your agent from `ryder_cup_prediction.root_agent`
2. See the `MCPToolset` configuration
3. Spawn the MCP server automatically
4. Make the tools available to the agent
5. Open the web UI for you to interact with the agent

## Debugging

If you need to debug the MCP server:
- Check `mcp_server.log` for server-side logs
- The log includes when the server starts, tool calls made, and any errors
- Lint errors about unresolved imports are expected during development and won't affect runtime

## Benefits

- **Automatic lifecycle management**: No need to start/stop the MCP server manually
- **Stdio communication**: More reliable than network-based communication for local development
- **Integrated debugging**: All logs and errors are captured in one place
- **Environment consistency**: Uses the same Python interpreter for both agent and server
