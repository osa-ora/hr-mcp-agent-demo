import os
import httpx
import asyncio
from fastmcp import FastMCP

# =========================================================
# CONFIGURATION
# =========================================================
# Hardcoded local server connection configurations to match your deployment style
MCP_HOST = "0.0.0.0"
WEATHER_MCP_PORT = 8060
MCP_TRANSPORT = "http"

# =========================================================
# DATA LAYER (MOCK INTERNAL WEATHER DB)
# =========================================================
MOCK_WEATHER = {
    "dubai": {"temp": "38°C", "condition": "Sunny ☀️", "wind": "12 km/h 💨"},
    "london": {"temp": "16°C", "condition": "Rainy 🌧️", "wind": "22 km/h 💨"},
    "new york": {"temp": "22°C", "condition": "Cloudy ☁️", "wind": "15 km/h 🍃"},
    "cairo": {"temp": "30°C", "condition": "Clear Sky 😎", "wind": "8 km/h 🍃"}
}

def fetch_local_weather(city: str) -> dict:
    normalized_city = city.lower().strip()
    # Default fallback data if the model asks for a city not explicitly listed above
    return MOCK_WEATHER.get(
        normalized_city, 
        {"temp": "24°C", "condition": "Partly Cloudy 100% ⛅", "wind": "10 km/h 🍃"}
    )

# =========================================================
# MCP SERVER INITIALIZATION
# =========================================================
mcp = FastMCP("Weather MCP")

# ---------------------------------------------------------
# TOOL 1: Today's Weather
# ---------------------------------------------------------
@mcp.tool(
    annotations={"skill": "weather"},
    description="Get current weather details for a city. The only parameter is 'city' (string)."
)
def get_today_weather(city: str) -> str:
    data = fetch_local_weather(city)
    return (
        f"Today's weather in {city.title()}: {data['temp']}, "
        f"{data['condition']} with wind speeds of {data['wind']}."
    )

# ---------------------------------------------------------
# TOOL 2: Historical / Future Weather by Date
# ---------------------------------------------------------
@mcp.tool(
    annotations={"skill": "weather"},
    description="Get weather for a city on a specific date. Required parameters: 'city' (string) and 'date_str' (string format YYYY-MM-DD)."
)
def get_date_weather(city: str, date_str: str) -> str:
    data = fetch_local_weather(city)
    return (
        f"Weather in {city.title()} on {date_str}: {data['temp']}, "
        f"{data['condition']} (Wind: {data['wind']})."
    )

# =========================================================
# MAIN ENTRY
# =========================================================
if __name__ == "__main__":
    print("REGISTERED TOOLS:", mcp.list_tools())

    mcp.run(
        transport=MCP_TRANSPORT,
        host=MCP_HOST,
        port=WEATHER_MCP_PORT
    )