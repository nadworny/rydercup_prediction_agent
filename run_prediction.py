# run_prediction.py
"""
Main executable script for the Ryder Cup Prediction Agent (Phase 1).

This script:
1. Launches the DataGolf MCP server as a subprocess
2. Connects an MCP client to the server
3. Creates MCP tool wrappers
4. Creates the agent with MCP tools enabled
5. Invokes the prediction workflow
"""


import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent
import sys

sys.path.insert(0, str(project_root))

# Import the agent builder function
from agent.agent import create_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """
    Main async function that orchestrates the entire prediction workflow.
    """

    print("=" * 80)
    print("RYDER CUP PREDICTION AGENT - PHASE 1")
    print("=" * 80)
    print()

    # -------------------------------------------------------------------------
    # Step 1: Launch the DataGolf MCP Server
    # -------------------------------------------------------------------------
    print("Step 1: Launching DataGolf MCP Server...")

    # Path to the MCP server script
    server_script_path = project_root / "mcp_servers" / "datagolf_server.py"

    # Server parameters for stdio transport
    server_params = StdioServerParameters(command="python", args=[str(server_script_path)], env=None)

    # -------------------------------------------------------------------------
    # Step 2: Connect MCP Client and Create Tool Wrappers
    # -------------------------------------------------------------------------
    print("Step 2: Connecting MCP Client...")

    # Use the stdio_client context manager to connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            # Initialize the session
            await mcp_session.initialize()

            # List available tools from the MCP server
            tools_response = await mcp_session.list_tools()
            print(f"  ✓ Found {len(tools_response.tools)} tool(s) from DataGolf MCP Server")

            # Create tool wrapper for getPlayerTrueStrokesGained
            async def getPlayerTrueStrokesGained(player_name: str) -> dict:
                """
                Retrieves the 2-year and 3-month True Strokes Gained data for a specific golfer.
                Args:
                    player_name: The full name of the golfer (e.g., "Scottie Scheffler").
                """
                result = await mcp_session.call_tool(
                    "getPlayerTrueStrokesGained", arguments={"player_name": player_name}
                )
                return result.content[0].text if result.content else {}

            mcp_tool_wrappers = [getPlayerTrueStrokesGained]

            for tool in tools_response.tools:
                print(f"    - {tool.name}: {tool.description}")
            print()

            # -------------------------------------------------------------------------
            # Step 3: Create Agent with MCP Tools
            # -------------------------------------------------------------------------
            print("Step 3: Creating agent with MCP tools...")

            # Create the agent with MCP tool wrappers
            agent = create_agent(mcp_tool_wrappers=mcp_tool_wrappers)

            print("  ✓ Agent created with MCP-enabled PlayerProfilerAgent")
            print()

            # -------------------------------------------------------------------------
            # Step 4: Prepare prompt and execute
            # -------------------------------------------------------------------------
            print("Step 4: Preparing prompt and executing workflow...")
            print()

            # Define the Sunday singles pairings for 2025
            pairings = [
                ("Cameron Young", "Justin Rose"),
                ("Justin Thomas", "Tommy Fleetwood"),
                ("Bryson DeChambeau", "Matt Fitzpatrick"),
                ("Patrick Cantlay", "Ludvig Åberg"),
                ("Xander Schauffele", "Jon Rahm"),
                ("J.J. Spaun", "Sepp Straka"),
                ("Russell Henley", "Shane Lowry"),
                ("Ben Griffin", "Rasmus Højgaard"),
                ("Collin Morikawa", "Tyrrell Hatton"),
                ("Sam Burns", "Robert MacIntyre"),
                ("Harris English", "Viktor Hovland"),
                ("Scottie Scheffler", "Rory McIlroy"),
            ]

            starting_score = {"USA": 8.5, "Europe": 9.5}

            pairings_text = "\n".join(
                [f"Match {i+1}: {usa} (USA) vs {eur} (Europe)" for i, (usa, eur) in enumerate(pairings)]
            )

            user_prompt = f"""
Analyze the Sunday singles matches for the 2025 Ryder Cup.

Current Score (after Saturday):
- USA: {starting_score['USA']}
- Europe: {starting_score['Europe']}

Sunday Singles Pairings:
{pairings_text}

Your task:
1. For the first match (Cameron Young vs Justin Rose):
   - Use the sequential pipeline to analyze this match
   - The pipeline will automatically:
     a) Profile both players (PlayerProfilerAgent)
     b) Analyze recent form (RecentFormAnalyst)
     c) Analyze baseline skill (BaselineSkillAnalyst)
     d) Synthesize probabilities (MatchupSynthesizerAgent)
     e) Generate outcome (MonteCarloSimulationAgent)
2. Report the result for this match
3. Show how the pipeline stages communicate via session.state

Begin your analysis now.
"""

            # Verify API key is set
            if not os.getenv("GOOGLE_API_KEY"):
                print("ERROR: GOOGLE_API_KEY not found in environment variables!")
                print("Please set it in .env file or export GOOGLE_API_KEY=your-key")
                return

            print(f"✓ Google API Key detected: {os.getenv('GOOGLE_API_KEY')[:20]}...")
            print()

            # Create session service and runner
            session_service = InMemorySessionService()
            runner = Runner(app_name="ryder_cup_predictor", agent=agent, session_service=session_service)

            print("✓ Runner initialized with InMemorySessionService")
            print()
            print("Executing coordinator agent...")
            print("-" * 80)
            print()

            # Create session for the conversation
            session = await session_service.create_session(app_name="ryder_cup_predictor", user_id="predictor_user")

            # Prepare user message
            user_message = types.Content(role="user", parts=[types.Part(text=user_prompt)])

            # Execute the agent and collect response
            final_response = ""
            async for event in runner.run_async(
                user_id=session.user_id, session_id=session.id, new_message=user_message
            ):
                # Print all events for visibility
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(part.text)
                            final_response = part.text

            print()
            print("-" * 80)
            print("EXECUTION COMPLETE!")
            print("-" * 80)
            print()
            print("=" * 80)
            print("PHASE 1 POC COMPLETE!")
            print("=" * 80)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
