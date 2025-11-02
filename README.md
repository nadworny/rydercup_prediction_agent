# Ryder Cup Prediction Agent

A multi-agent system powered by Google ADK and Model Context Protocol (MCP) that predicts Ryder Cup match outcomes using True Strokes Gained (TSG) data.

## Architecture

The system uses a **Sequential Agent Pipeline** with 5 specialized sub-agents:

1. **PlayerProfilerAgent** - Fetches TSG data via MCP tools
2. **RecentFormAnalyst** - Analyzes 3-month form trends
3. **BaselineSkillAnalyst** - Evaluates 2-year baseline skill
4. **MatchupSynthesizerAgent** - Synthesizes probabilities from form + skill
5. **MonteCarloSimulationAgent** - Generates match outcomes

All agents communicate via `session.state` using `output_key` parameters.

## Prerequisites

- Python 3.11+
- Google API Key (for Gemini models)
- AgentOps API Key (optional, for tracing)

## Installation

```bash
# Install dependencies
uv sync

# Create .env file from example
cp .env.example .env
# Then edit .env and add your API keys
```

## Usage

### Option 1: CLI Execution (with MCP tools)

Run the full agent system with live MCP data access:

```bash
python run_prediction.py
```

This launches:
- DataGolf MCP server (stdio transport)
- Agent pipeline with MCP tool integration
- Gemini 2.5 Flash model for inference
- AgentOps tracing (if configured)

### Option 2: ADK Web UI (visualization mode)

Launch the interactive web interface to visualize agent hierarchy and execution:

```bash
adk web agent --port 8080
```

Then open http://127.0.0.1:8080 in your browser.

**Note:** The web UI uses a simplified agent without MCP tools for compatibility. For full MCP functionality, use CLI execution.

## Project Structure

```
.
├── agent/
│   ├── agent.py                    # Agent builder with MCP support
│   └── sub_agent_definitions.py   # Agent prompts and configs
├── mcp_servers/
│   └── datagolf_server.py          # FastMCP server with TSG data
├── run_prediction.py               # CLI entry point
└── .env                            # Environment variables
```

## Key Features

- **MCP Integration**: Live data fetching via Model Context Protocol
- **Sequential Pipeline**: Agents execute in order, sharing state
- **Flexible Tool Injection**: `create_agent(mcp_tool_wrappers)` supports both MCP-enabled and tool-free modes
- **AgentOps Tracing**: Optional LLM observability
- **ADK Web UI**: Visual agent hierarchy and execution monitoring

## Development

The `create_agent()` function in `agent/agent.py` accepts optional MCP tool wrappers:

```python
# With MCP tools (CLI mode)
agent = create_agent(mcp_tool_wrappers=[getPlayerTrueStrokesGained])

# Without tools (Web UI mode)
agent = create_agent()  # or create_agent(mcp_tool_wrappers=None)
```

This design allows the same agent definition to work in both execution contexts.
