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

load_dotenv()

project_root = Path(__file__).parent

from ryder_cup_prediction.agent import create_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Main async function that orchestrates the entire prediction workflow."""

    server_script_path = project_root / "mcp_servers" / "datagolf_server.py"
    server_params = StdioServerParameters(command="python", args=[str(server_script_path)], env=None)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()

            tools_response = await mcp_session.list_tools()

            async def getPlayerTrueStrokesGained(player_name: str) -> dict:
                """Retrieves the 2-year and 3-month True Strokes Gained data for a specific golfer."""
                result = await mcp_session.call_tool(
                    "getPlayerTrueStrokesGained", arguments={"player_name": player_name}
                )
                return result.content[0].text if result.content else {}

            mcp_tool_wrappers = [getPlayerTrueStrokesGained]
            agent = create_agent(mcp_tool_wrappers=mcp_tool_wrappers)

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

            if not os.getenv("GOOGLE_API_KEY"):
                print("ERROR: GOOGLE_API_KEY not found in environment variables!")
                return

            session_service = InMemorySessionService()
            runner = Runner(app_name="ryder_cup_prediction", agent=agent, session_service=session_service)

            session = await session_service.create_session(app_name="ryder_cup_prediction", user_id="predictor_user")
            user_message = types.Content(role="user", parts=[types.Part(text=user_prompt)])

            async for event in runner.run_async(
                user_id=session.user_id, session_id=session.id, new_message=user_message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(part.text)


if __name__ == "__main__":
    asyncio.run(main())
