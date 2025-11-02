import os

import agentops
from ryder_cup_prediction.sub_agent_definitions import MASTER_INSTRUCTIONS
from ryder_cup_prediction.sub_agent_definitions import get_sub_agents
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents import SequentialAgent

AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY, default_tags=["google adk"])

# Load environment variables
load_dotenv()

def create_agent(mcp_tool_wrappers=None):
    """
    Creates the Ryder Cup prediction agent with optional MCP tools.

    Args:
        mcp_tool_wrappers: List of MCP tool wrapper functions. If None, creates
                          agent without MCP tools (for web UI compatibility).

    Returns:
        LlmAgent: The root coordinator agent with sequential pipeline
    """
    # Use empty list if no tools provided
    tools = mcp_tool_wrappers if mcp_tool_wrappers is not None else []

    # Get sub-agent configurations
    sub_agents_configs = get_sub_agents(tools)

    # 1. PlayerProfilerAgent (with MCP tools if provided)
    player_profiler = LlmAgent(
        name="PlayerProfilerAgent",
        description="Profiles all 24 players by fetching TSG data",
        instruction=sub_agents_configs[0]["prompt"],
        tools=sub_agents_configs[0].get("tools", []),
        model="gemini-2.5-flash",
        output_key="player_profiles",
    )

    # 2. RecentFormAnalyst
    recent_form_analyst = LlmAgent(
        name="RecentFormAnalyst",
        description="Analyzes 3-month recent form trends",
        instruction=sub_agents_configs[1]["prompt"] + "\n\nAccess player data from session.state['player_profiles']",
        model="gemini-2.5-flash",
        output_key="recent_form_analysis",
    )

    # 3. BaselineSkillAnalyst
    baseline_skill_analyst = LlmAgent(
        name="BaselineSkillAnalyst",
        description="Analyzes 2-year baseline skill levels",
        instruction=sub_agents_configs[2]["prompt"] + "\n\nAccess player data from session.state['player_profiles']",
        model="gemini-2.5-flash",
        output_key="baseline_skill_analysis",
    )

    # 4. MatchupSynthesizerAgent
    matchup_synthesizer = LlmAgent(
        name="MatchupSynthesizerAgent",
        description="Synthesizes form + skill into match probabilities",
        instruction=sub_agents_configs[3]["prompt"]
        + "\n\nAccess analysis from session.state['recent_form_analysis'] and session.state['baseline_skill_analysis']",
        model="gemini-2.5-flash",
        output_key="match_probabilities",
    )

    # 5. MonteCarloSimulationAgent
    monte_carlo_simulator = LlmAgent(
        name="MonteCarloSimulationAgent",
        description="Runs discrete outcome simulation",
        instruction=sub_agents_configs[4]["prompt"]
        + "\n\nAccess probabilities from session.state['match_probabilities']",
        model="gemini-2.5-flash",
        output_key="simulation_results",
    )

    # Create SequentialAgent to orchestrate the pipeline
    match_analysis_pipeline = SequentialAgent(
        name="MatchAnalysisPipeline",
        description="Sequential pipeline for analyzing one match",
        sub_agents=[
            player_profiler,
            recent_form_analyst,
            baseline_skill_analyst,
            matchup_synthesizer,
            monte_carlo_simulator,
        ],
    )

    # Create coordinator agent that delegates to the pipeline
    coordinator = LlmAgent(
        name="RyderCupCoordinator",
        description="Coordinates analysis of all 12 Ryder Cup matches using sequential pipeline",
        instruction=MASTER_INSTRUCTIONS,
        sub_agents=[match_analysis_pipeline],
        model="gemini-2.5-flash",
    )

    return coordinator


root_agent = create_agent()
