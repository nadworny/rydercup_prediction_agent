import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("DataGolf")

# Mock data for Phase 1.
# This simulates the data we'd get from the DataGolf API.
MOCK_PLAYER_DATA = {
    "Scottie Scheffler": {
        "2-year": {"total_sg": 2.85, "off_the_tee": 0.95, "approach": 1.25, "around_the_green": 0.35, "putting": 0.30},
        "3-month": {"total_sg": 3.10, "off_the_tee": 1.05, "approach": 1.35, "around_the_green": 0.40, "putting": 0.30}
    },
    "Rory McIlroy": {
        "2-year": {"total_sg": 2.65, "off_the_tee": 1.10, "approach": 0.90, "around_the_green": 0.25, "putting": 0.40},
        "3-month": {"total_sg": 2.40, "off_the_tee": 1.00, "approach": 0.80, "around_the_green": 0.20, "putting": 0.40}
    },
    "Cameron Young": {
        "2-year": {"total_sg": 1.80, "off_the_tee": 0.80, "approach": 0.60, "around_the_green": 0.10, "putting": 0.30},
        "3-month": {"total_sg": 1.95, "off_the_tee": 0.85, "approach": 0.65, "around_the_green": 0.10, "putting": 0.35}
    },
    "Justin Rose": {
        "2-year": {"total_sg": 1.40, "off_the_tee": 0.30, "approach": 0.70, "around_the_green": 0.20, "putting": 0.20},
        "3-month": {"total_sg": 1.50, "off_the_tee": 0.35, "approach": 0.75, "around_the_green": 0.15, "putting": 0.25}
    },
    "Justin Thomas": {
        "2-year": {"total_sg": 1.90, "off_the_tee": 0.50, "approach": 1.00, "around_the_green": 0.30, "putting": 0.10},
        "3-month": {"total_sg": 1.70, "off_the_tee": 0.45, "approach": 0.90, "around_the_green": 0.25, "putting": 0.10}
    },
    "Tommy Fleetwood": {
        "2-year": {"total_sg": 1.85, "off_the_tee": 0.60, "approach": 0.75, "around_the_green": 0.25, "putting": 0.25},
        "3-month": {"total_sg": 2.00, "off_the_tee": 0.65, "approach": 0.80, "around_the_green": 0.25, "putting": 0.30}
    },
    "Bryson DeChambeau": {
        "2-year": {"total_sg": 2.00, "off_the_tee": 1.20, "approach": 0.40, "around_the_green": 0.10, "putting": 0.30},
        "3-month": {"total_sg": 2.10, "off_the_tee": 1.30, "approach": 0.40, "around_the_green": 0.05, "putting": 0.35}
    },
    "Matt Fitzpatrick": {
        "2-year": {"total_sg": 1.75, "off_the_tee": 0.40, "approach": 0.60, "around_the_green": 0.30, "putting": 0.45},
        "3-month": {"total_sg": 1.80, "off_the_tee": 0.40, "approach": 0.65, "around_the_green": 0.30, "putting": 0.45}
    },
    "Patrick Cantlay": {
        "2-year": {"total_sg": 2.10, "off_the_tee": 0.60, "approach": 0.80, "around_the_green": 0.20, "putting": 0.50},
        "3-month": {"total_sg": 2.00, "off_the_tee": 0.55, "approach": 0.75, "around_the_green": 0.20, "putting": 0.50}
    },
    "Ludvig Åberg": {
        "2-year": {"total_sg": 2.20, "off_the_tee": 1.00, "approach": 0.80, "around_the_green": 0.10, "putting": 0.30},
        "3-month": {"total_sg": 2.30, "off_the_tee": 1.10, "approach": 0.85, "around_the_green": 0.10, "putting": 0.25}
    },
    "Xander Schauffele": {
        "2-year": {"total_sg": 2.15, "off_the_tee": 0.70, "approach": 0.80, "around_the_green": 0.25, "putting": 0.40},
        "3-month": {"total_sg": 2.20, "off_the_tee": 0.70, "approach": 0.80, "around_the_green": 0.25, "putting": 0.45}
    },
    "Jon Rahm": {
        "2-year": {"total_sg": 2.50, "off_the_tee": 0.90, "approach": 0.95, "around_the_green": 0.30, "putting": 0.35},
        "3-month": {"total_sg": 2.45, "off_the_tee": 0.85, "approach": 0.90, "around_the_green": 0.30, "putting": 0.40}
    },
    "J.J. Spaun": {
        "2-year": {"total_sg": 0.80, "off_the_tee": 0.20, "approach": 0.40, "around_the_green": 0.05, "putting": 0.15},
        "3-month": {"total_sg": 0.75, "off_the_tee": 0.15, "approach": 0.35, "around_the_green": 0.05, "putting": 0.20}
    },
    "Sepp Straka": {
        "2-year": {"total_sg": 1.10, "off_the_tee": 0.30, "approach": 0.70, "around_the_green": 0.00, "putting": 0.10},
        "3-month": {"total_sg": 1.20, "off_the_tee": 0.35, "approach": 0.75, "around_the_green": 0.00, "putting": 0.10}
    },
    "Russell Henley": {
        "2-year": {"total_sg": 1.50, "off_the_tee": 0.10, "approach": 0.90, "around_the_green": 0.20, "putting": 0.30},
        "3-month": {"total_sg": 1.40, "off_the_tee": 0.10, "approach": 0.80, "around_the_green": 0.20, "putting": 0.30}
    },
    "Shane Lowry": {
        "2-year": {"total_sg": 1.45, "off_the_tee": 0.30, "approach": 0.65, "around_the_green": 0.35, "putting": 0.15},
        "3-month": {"total_sg": 1.55, "off_the_tee": 0.35, "approach": 0.70, "around_the_green": 0.35, "putting": 0.15}
    },
    "Ben Griffin": {
        "2-year": {"total_sg": 0.90, "off_the_tee": 0.25, "approach": 0.40, "around_the_green": 0.10, "putting": 0.15},
        "3-month": {"total_sg": 1.00, "off_the_tee": 0.30, "approach": 0.45, "around_the_green": 0.10, "putting": 0.15}
    },
    "Rasmus Højgaard": {
        "2-year": {"total_sg": 1.00, "off_the_tee": 0.50, "approach": 0.30, "around_the_green": 0.05, "putting": 0.15},
        "3-month": {"total_sg": 1.10, "off_the_tee": 0.55, "approach": 0.30, "around_the_green": 0.05, "putting": 0.20}
    },
    "Collin Morikawa": {
        "2-year": {"total_sg": 1.95, "off_the_tee": 0.30, "approach": 1.20, "around_the_green": 0.15, "putting": 0.30},
        "3-month": {"total_sg": 1.85, "off_the_tee": 0.25, "approach": 1.10, "around_the_green": 0.15, "putting": 0.35}
    },
    "Tyrrell Hatton": {
        "2-year": {"total_sg": 1.80, "off_the_tee": 0.50, "approach": 0.70, "around_the_green": 0.20, "putting": 0.40},
        "3-month": {"total_sg": 1.90, "off_the_tee": 0.55, "approach": 0.70, "around_the_green": 0.20, "putting": 0.45}
    },
    "Sam Burns": {
        "2-year": {"total_sg": 1.60, "off_the_tee": 0.40, "approach": 0.40, "around_the_green": 0.10, "putting": 0.70},
        "3-month": {"total_sg": 1.50, "off_the_tee": 0.35, "approach": 0.35, "around_the_green": 0.10, "putting": 0.70}
    },
    "Robert MacIntyre": {
        "2-year": {"total_sg": 1.20, "off_the_tee": 0.40, "approach": 0.50, "around_the_green": 0.10, "putting": 0.20},
        "3-month": {"total_sg": 1.30, "off_the_tee": 0.45, "approach": 0.55, "around_the_green": 0.10, "putting": 0.20}
    },
    "Harris English": {
        "2-year": {"total_sg": 1.00, "off_the_tee": 0.20, "approach": 0.30, "around_the_green": 0.20, "putting": 0.30},
        "3-month": {"total_sg": 0.90, "off_the_tee": 0.15, "approach": 0.25, "around_the_green": 0.20, "putting": 0.30}
    },
    "Viktor Hovland": {
        "2-year": {"total_sg": 2.25, "off_the_tee": 0.80, "approach": 1.00, "around_the_green": -0.10, "putting": 0.55},
        "3-month": {"total_sg": 2.40, "off_the_tee": 0.85, "approach": 1.05, "around_the_green": -0.05, "putting": 0.55}
    }
}

@mcp.tool()
async def getPlayerTrueStrokesGained(player_name: str) -> dict:
    """
    Retrieves the 2-year and 3-month True Strokes Gained data for a specific golfer.
    Args:
        player_name: The full name of the golfer (e.g., "Scottie Scheffler").
    """
    # Simulate network delay
    await asyncio.sleep(0.1) 
    
    data = MOCK_PLAYER_DATA.get(player_name)
    if not data:
        return {"error": f"No data found for player: {player_name}"}
    
    # Return data for both time periods as required by Phase 1 agents
    return {
        "2-year": data["2-year"],
        "3-month": data["3-month"]
    }

def main():
    # Run the server using stdio transport
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
