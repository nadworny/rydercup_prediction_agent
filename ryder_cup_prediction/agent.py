import os
import sys

import agentops
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents import SequentialAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from ryder_cup_prediction.sub_agent_definitions import MASTER_INSTRUCTIONS
from ryder_cup_prediction.sub_agent_definitions import get_sub_agents

AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY, default_tags=["google adk"])

# Load environment variables
load_dotenv()


def create_agent(mcp_tool_wrappers=None):
    """
    Creates the Ryder Cup prediction agent with MCP tools.

    The MCP server is automatically spawned as a subprocess by the adk runner
    when the agent starts, and communicates via stdio.

    Args:
        mcp_tool_wrappers: Deprecated parameter for backward compatibility.
                          MCP tools are now automatically loaded via MCPToolset.

    Returns:
        LlmAgent: The root coordinator agent with sequential pipeline
    """
    # --- Configuration to find the MCP script ---

    # Get the absolute path to the Python executable that is currently running
    python_executable = sys.executable

    # Get the directory where this agent.py file is located
    current_dir = os.path.dirname(__file__)

    # Find the mcp_servers directory and the datagolf_server.py script
    mcp_script_path = os.path.abspath(os.path.join(current_dir, "..", "mcp_servers", "datagolf_server.py"))

    # --- Toolset Configuration ---

    # 1. Define the command to run the MCP server
    mcp_server_config = StdioServerParameters(command=python_executable, args=[mcp_script_path])

    # 2. Define the connection parameters
    mcp_connection_config = StdioConnectionParams(
        server_params=mcp_server_config, timeout=10  # Timeout for the server to start (in seconds)
    )

    # 3. Create the MCPToolset instance
    # The adk runner will automatically start and stop the MCP server
    managed_mcp_tools = MCPToolset(connection_params=mcp_connection_config)

    # Get sub-agent configurations with MCP toolset
    sub_agents_configs = get_sub_agents([managed_mcp_tools])

    # 1. PlayerProfilerAgent (with MCP tools)
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
    # The SequentialAgent itself acts as the coordinator
    coordinator = SequentialAgent(
        name="RyderCupCoordinator",
        description=MASTER_INSTRUCTIONS,
        sub_agents=[
            player_profiler,
            recent_form_analyst,
            baseline_skill_analyst,
            matchup_synthesizer,
            monte_carlo_simulator,
        ],
    )

    return coordinator


root_agent = create_agent()
