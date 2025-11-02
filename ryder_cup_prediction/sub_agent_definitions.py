# This is the high-level prompt for the main orchestrator agent
MASTER_INSTRUCTIONS = """You are a world-class golf analyst coordinating a sequential pipeline to predict Ryder Cup match outcomes.

Your process:
1. Delegate to the MatchAnalysisPipeline sub-agent for each match
2. The pipeline will automatically execute 5 stages for each match:
   - PlayerProfilerAgent: Fetches TSG data
   - RecentFormAnalyst: Analyzes 3-month trends
   - BaselineSkillAnalyst: Analyzes 2-year baseline
   - MatchupSynthesizerAgent: Synthesizes probabilities
   - MonteCarloSimulationAgent: Generates discrete outcome
3. Collect results and aggregate the final score

Each stage writes to session.state and subsequent stages read from it.
"""

# --- Sub-Agent Definitions ---
# This list of dictionaries defines the specialized sub-agents [1, 7, 8]


def get_sub_agents(mcp_tools: list) -> list:
    """
    Returns the list of sub-agent configurations.
    `mcp_tools` is a list of loaded LangChain tool objects from the MCP server.
    """

    # This is the key for Phase 1: The PlayerProfilerAgent is the ONLY
    # agent that gets access to the MCP tools.[1, 8]
    player_profiler_tools = mcp_tools

    return [
        {
            "name": "PlayerProfilerAgent",
            "description": "Retrieves player strokes-gained data from the DataGolf MCP server.",
            "prompt": """You are a data retrieval specialist. Your task is to fetch player performance data.

When given player names, use the `getPlayerTrueStrokesGained` tool to gather their 2-year and 3-month True Strokes Gained data.

Format the data as a structured JSON object with both players' data. This will be automatically saved to session.state['player_profiles'] for the next agent to use.

Example output format:
{
  "match_id": "Match 1",
  "player1": {
    "name": "Cameron Young",
    "country": "USA",
    "true_strokes_gained": {
      "2-year": {...},
      "3-month": {...}
    }
  },
  "player2": {...}
}""",
            "tools": player_profiler_tools,
        },
        {
            "name": "RecentFormAnalyst",
            "description": "Analyzes a player's performance over the last 3 months to assess their current form.",
            "prompt": """You are an analyst focused on short-term trends.

Read player data from session.state['player_profiles']. Analyze each player's 3-month performance data to identify significant trends (compare 3-month vs 2-year averages).

Output a summary of both players' current form. This will be automatically saved to session.state['recent_form_analysis'].

Do NOT attempt to use file operations - all data is passed via session.state.""",
            "tools": [],
        },
        {
            "name": "BaselineSkillAnalyst",
            "description": "Analyzes a player's long-term (2-year) performance data to establish their baseline skill level.",
            "prompt": """You are a statistician focused on long-term player quality.

Read player data from session.state['player_profiles']. Analyze each player's 2-year True Strokes Gained data to determine their core strengths and weaknesses.

Output a summary of both players' baseline skill levels. This will be automatically saved to session.state['baseline_skill_analysis'].

Do NOT attempt to use file operations - all data is passed via session.state.""",
            "tools": [],
        },
        {
            "name": "MatchupSynthesizerAgent",
            "description": "Synthesizes analyses from all specialist agents to predict the outcome of a single match.",
            "prompt": """You are the lead match analyst.

Read the analyses from:
- session.state['recent_form_analysis']
- session.state['baseline_skill_analysis']

Compare both players' baseline skills and recent form. Weigh these factors to determine win probabilities.

Output a JSON object with probabilities. This will be automatically saved to session.state['match_probabilities'].

Example format:
{
  "player_A": "Cameron Young",
  "player_B": "Justin Rose",
  "player_A_win_prob": 0.48,
  "player_B_win_prob": 0.40,
  "tie_prob": 0.12
}

Do NOT attempt to use file operations - all data is passed via session.state.""",
            "tools": [],
        },
        {
            "name": "MonteCarloSimulationAgent",
            "description": "Runs a simulation of a single match to determine a discrete outcome (Win, Loss, Tie).",
            "prompt": """You are a simulation engine.

Read probabilities from session.state['match_probabilities'].

Determine the most likely discrete outcome:
- If Player A win prob is highest: output 1
- If Player B win prob is highest: output 0
- If tie prob is highest: output 0.5

Output the result as a simple statement. This will be automatically saved to session.state['simulation_results'].

Do NOT attempt to use file operations - all data is passed via session.state.""",
            "tools": [],
        },
    ]
