# Architecture Diagram

## Phase 1: Ryder Cup Prediction Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          run_prediction.py (main)                           │
│                                                                             │
│  1. Launch MCP Server (subprocess via stdio)                               │
│  2. Connect MCP Client                                                     │
│  3. Convert MCP tools to LangChain tools                                   │
│  4. Create Deep Agent                                                      │
│  5. Run prediction workflow                                                │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
                            │ async
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MCP Layer (stdio transport)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────┐                                │
│  │   DataGolf MCP Server (FastMCP)        │                                │
│  │   File: mcp_servers/datagolf_server.py │                                │
│  │                                        │                                │
│  │   Tool: getPlayerTrueStrokesGained     │                                │
│  │   - Input: player_name (str)           │                                │
│  │   - Output: {                          │                                │
│  │       "2-year": {...},                 │                                │
│  │       "3-month": {...}                 │                                │
│  │     }                                  │                                │
│  │   - Mock data for 24 players           │                                │
│  └────────────────────────────────────────┘                                │
│                                                                             │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
                            │ convert_mcp_to_langchain_tool
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Agent Layer (Google ADK)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Master Agent (Deep Agent)                      │   │
│  │  Instructions: MASTER_INSTRUCTIONS                                  │   │
│  │  Model: claude-3-7-sonnet-20250219                                  │   │
│  │                                                                     │   │
│  │  Workflow:                                                          │   │
│  │  1. Plan (write_todos)                                              │   │
│  │  2. Profile all 24 players                                          │   │
│  │  3. Analyze 12 matches                                              │   │
│  │  4. Aggregate results                                               │   │
│  └───────────────────────┬─────────────────────────────────────────────┘   │
│                          │                                                 │
│                          │ delegates to                                    │
│                          ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Sub-Agents (5 agents)                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  1. PlayerProfilerAgent                                             │   │
│  │     ├── Tools: [getPlayerTrueStrokesGained] ◄── ONLY MCP ACCESS    │   │
│  │     ├── Input: player_name                                          │   │
│  │     └── Output: {player_name}_profile.json                          │   │
│  │                                                                     │   │
│  │  2. RecentFormAnalyst                                               │   │
│  │     ├── Tools: [] (built-in file tools only)                        │   │
│  │     ├── Input: {player_name}_profile.json                           │   │
│  │     └── Output: {player_name}_form.txt                              │   │
│  │                                                                     │   │
│  │  3. BaselineSkillAnalyst                                            │   │
│  │     ├── Tools: [] (built-in file tools only)                        │   │
│  │     ├── Input: {player_name}_profile.json                           │   │
│  │     └── Output: {player_name}_skill.txt                             │   │
│  │                                                                     │   │
│  │  4. MatchupSynthesizerAgent                                         │   │
│  │     ├── Tools: [] (built-in file tools only)                        │   │
│  │     ├── Input: *_form.txt, *_skill.txt                              │   │
│  │     └── Output: match_N_probs.json                                  │   │
│  │                                                                     │   │
│  │  5. MonteCarloSimulationAgent                                       │   │
│  │     ├── Tools: [] (built-in file tools only)                        │   │
│  │     ├── Input: match_N_probs.json                                   │   │
│  │     └── Output: match_N_result.txt (1, 0.5, or 0)                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
                            │ uses
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Virtual File System (VFS)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Files created during execution:                                           │
│                                                                             │
│  Player Profiles (24 files):                                               │
│  ├── Scottie_Scheffler_profile.json                                        │
│  ├── Rory_McIlroy_profile.json                                             │
│  └── ... (22 more players)                                                 │
│                                                                             │
│  Form Analysis (24 files):                                                 │
│  ├── Scottie_Scheffler_form.txt                                            │
│  ├── Rory_McIlroy_form.txt                                                 │
│  └── ... (22 more players)                                                 │
│                                                                             │
│  Skill Analysis (24 files):                                                │
│  ├── Scottie_Scheffler_skill.txt                                           │
│  ├── Rory_McIlroy_skill.txt                                                │
│  └── ... (22 more players)                                                 │
│                                                                             │
│  Match Probabilities (12 files):                                           │
│  ├── match_1_probs.json                                                    │
│  ├── match_2_probs.json                                                    │
│  └── ... (10 more matches)                                                 │
│                                                                             │
│  Match Results (12 files):                                                 │
│  ├── match_1_result.txt                                                    │
│  ├── match_2_result.txt                                                    │
│  └── ... (10 more matches)                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Sequence

```
1. run_prediction.py launches
   │
   ├─► Launch DataGolf MCP Server (subprocess)
   │
   ├─► Connect MCP Client via stdio
   │
   ├─► List tools: getPlayerTrueStrokesGained
   │
   ├─► Convert MCP tool → LangChain tool
   │
   ├─► Create Deep Agent with sub-agents
   │   │
   │   ├─► Master Agent (all built-in tools)
   │   │
   │   └─► Sub-Agents:
   │       ├─► PlayerProfilerAgent [getPlayerTrueStrokesGained]
   │       ├─► RecentFormAnalyst []
   │       ├─► BaselineSkillAnalyst []
   │       ├─► MatchupSynthesizerAgent []
   │       └─► MonteCarloSimulationAgent []
   │
   └─► Run prediction workflow
       │
       └─► Master Agent orchestrates:
           │
           ├─► Step 1: Create plan (write_todos)
           │
           ├─► Step 2: Profile 24 players
           │   │
           │   └─► For each player:
           │       ├─► Delegate to PlayerProfilerAgent
           │       ├─► Call getPlayerTrueStrokesGained(player)
           │       └─► Write {player}_profile.json
           │
           ├─► Step 3: Analyze 12 matches
           │   │
           │   └─► For each match:
           │       │
           │       ├─► Delegate to RecentFormAnalyst (player A)
           │       │   ├─► Read {playerA}_profile.json
           │       │   └─► Write {playerA}_form.txt
           │       │
           │       ├─► Delegate to RecentFormAnalyst (player B)
           │       │   ├─► Read {playerB}_profile.json
           │       │   └─► Write {playerB}_form.txt
           │       │
           │       ├─► Delegate to BaselineSkillAnalyst (player A)
           │       │   ├─► Read {playerA}_profile.json
           │       │   └─► Write {playerA}_skill.txt
           │       │
           │       ├─► Delegate to BaselineSkillAnalyst (player B)
           │       │   ├─► Read {playerB}_profile.json
           │       │   └─► Write {playerB}_skill.txt
           │       │
           │       ├─► Delegate to MatchupSynthesizerAgent
           │       │   ├─► Read all form/skill files
           │       │   └─► Write match_N_probs.json
           │       │
           │       └─► Delegate to MonteCarloSimulationAgent
           │           ├─► Read match_N_probs.json
           │           └─► Write match_N_result.txt
           │
           └─► Step 4: Aggregate results
               │
               ├─► Read all 12 match_N_result.txt files
               ├─► Sum discrete outcomes
               ├─► Add to starting score
               └─► Output: "Predicted Final Score: Europe X, USA Y"
```

## Key Architecture Principles

### 1. Data Isolation
- **Only PlayerProfilerAgent** has MCP tool access
- All other agents use virtual file system
- Creates clear separation of concerns

### 2. Async Throughout
- MCP server: async tool handler
- MCP client: async session management
- Agent creation: async_create_deep_agent
- Execution: asyncio.run(main())

### 3. Traceable Data Flow
- Virtual file system creates audit trail
- Each agent writes intermediate results
- Easy to debug and inspect workflow

### 4. Modular Design
- Each sub-agent has single responsibility
- Master agent orchestrates workflow
- Easy to add/remove/modify agents

### 5. Mock Data (Phase 1)
- Validates architecture before API integration
- Fast execution without network calls
- Deterministic for testing

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                           │
│  • run_prediction.py (main script)                              │
│  • agent/sub_agent_definitions.py (configs)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Framework Layer                              │
│  • Google ADK (agents package)                                  │
│    - async_create_deep_agent                                    │
│    - Built-in tools (write_todos, read_file, write_file)        │
│  • LangChain MCP Adapters (langchain_mcp_adapters)              │
│    - convert_mcp_to_langchain_tool                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Protocol Layer                               │
│  • Model Context Protocol (mcp package)                         │
│    - ClientSession                                              │
│    - StdioServerParameters                                      │
│    - stdio_client                                               │
│  • FastMCP (mcp.server.fastmcp)                                 │
│    - Server initialization                                      │
│    - Tool decorator (@mcp.tool())                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Layer                                  │
│  • Claude 3.7 Sonnet (claude-3-7-sonnet-20250219)               │
│  • Anthropic API (ANTHROPIC_API_KEY)                            │
└─────────────────────────────────────────────────────────────────┘
```

## File Organization

```
rydercup_predictor_agent_copilot/
│
├── mcp_servers/                    # MCP Server implementations
│   ├── __init__.py
│   └── datagolf_server.py          # Phase 1: DataGolf mock server
│       ├── FastMCP initialization
│       ├── MOCK_PLAYER_DATA (24 players)
│       ├── @mcp.tool() getPlayerTrueStrokesGained
│       └── main() with stdio transport
│
├── agent/                          # Agent configurations
│   ├── __init__.py
│   └── sub_agent_definitions.py
│       ├── MASTER_INSTRUCTIONS
│       └── get_sub_agents(mcp_tools)
│           ├── PlayerProfilerAgent [mcp_tools]
│           ├── RecentFormAnalyst []
│           ├── BaselineSkillAnalyst []
│           ├── MatchupSynthesizerAgent []
│           └── MonteCarloSimulationAgent []
│
├── run_prediction.py               # Main executable
│   ├── main() async function
│   ├── Launch MCP server
│   ├── Connect MCP client
│   ├── Create deep agent
│   └── Run prediction workflow
│
├── requirements.txt                # Dependencies
├── README.md                       # Full documentation
├── QUICK_START.md                  # Getting started guide
├── IMPLEMENTATION_SUMMARY.md       # Technical details
├── ARCHITECTURE.md                 # This file
├── .env.example                    # Environment template
└── .gitignore                      # Git exclusions
```

This architecture enables:
✅ Clear separation of concerns
✅ Easy testing and debugging
✅ Scalability for Phase 2+ (add more MCP servers)
✅ Traceable data flow
✅ Async efficiency
✅ Modular agent design
