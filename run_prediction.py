# run_prediction.py
"""
Main executable script for the Ryder Cup Prediction Agent (Phase 1).

This script invokes the prediction workflow using the agent
with MCP tools automatically managed by MCPToolset.
"""


import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from ryder_cup_prediction.agent import root_agent


async def main():
    """Main async function that orchestrates the entire prediction workflow."""

    pairings = [
        ("Justin Rose", "Cameron Young"),
        ("Tommy Fleetwood", "Justin Thomas"),
        ("Matt Fitzpatrick", "Bryson DeChambeau"),
        ("Rory McIlroy", "Scottie Scheffler"),
        ("Ludvig Åberg", "Patrick Cantlay"),
        ("Jon Rahm", "Xander Schauffele"),
        ("Sepp Straka", "J. J. Spaun"),
        ("Shane Lowry", "Russell Henley"),
        ("Rasmus Højgaard", "Ben Griffin"),
        ("Tyrrell Hatton", "Collin Morikawa"),
        ("Robert MacIntyre", "Sam Burns"),
        ("Viktor Hovland", "Harris English"),
    ]

    starting_score = {"USA": 4.5, "Europe": 11.5}

    pairings_text = "\n".join([f"Match {i+1}: {eur} (Europe) vs {usa} (USA)" for i, (eur, usa) in enumerate(pairings)])

    user_prompt = f"""
Analyze the Sunday singles matches for the 2025 Ryder Cup.

Current Score (after Saturday):
- USA: {starting_score['USA']}
- Europe: {starting_score['Europe']}

Sunday Singles Pairings (Europe player listed first):
{pairings_text}

Your task:
1. For the first match (Justin Rose vs Cameron Young):
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
    runner = Runner(app_name="ryder_cup_prediction", agent=root_agent, session_service=session_service)

    session = await session_service.create_session(app_name="ryder_cup_prediction", user_id="predictor_user")

    print("Prompt:")
    print(user_prompt)

    user_message = types.Content(role="user", parts=[types.Part(text=user_prompt)])

    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=user_message):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)


if __name__ == "__main__":
    asyncio.run(main())
