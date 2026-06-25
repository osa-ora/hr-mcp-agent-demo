import httpx
from fastmcp import FastMCP

# =========================================================
# CONFIGURATION
# =========================================================
MCP_HOST = "0.0.0.0"
WEATHER_MCP_PORT = 8060
MCP_TRANSPORT = "http"

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# =========================================================
# MCP SERVER
# =========================================================
mcp = FastMCP("Weather MCP")

# =========================================================
# INTERNAL HELPERS
# =========================================================
async def get_coordinates(city: str):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(GEOCODING_URL, params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        })

        data = r.json()

        if "results" not in data or not data["results"]:
            raise ValueError(f"City not found: {city}")

        loc = data["results"][0]
        return loc["latitude"], loc["longitude"], loc.get("name", city)


async def get_weather(lat: float, lon: float):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(WEATHER_URL, params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True
        })

        return r.json().get("current_weather", {})

# =========================================================
# TOOL 1: CURRENT WEATHER
# =========================================================
@mcp.tool(
    annotations={"skill": "weather"},
    description="Get current weather details for a city."
)
async def get_today_weather(city: str) -> str:
    lat, lon, resolved_city = await get_coordinates(city)
    weather = await get_weather(lat, lon)

    return (
        f"Today's weather in {resolved_city.title()}: "
        f"{weather.get('temperature')}°C, "
        f"Wind {weather.get('windspeed')} km/h, "
        f"Weather code {weather.get('weathercode')}."
    )

# =========================================================
# TOOL 2: DATE WEATHER (approx via current snapshot fallback)
# =========================================================
@mcp.tool(
    annotations={"skill": "weather"},
    description="Get weather for a city on a specific date (uses live data approximation)."
)
async def get_date_weather(city: str, date_str: str) -> str:
    lat, lon, resolved_city = await get_coordinates(city)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone": "auto"
            }
        )

        data = r.json()

    try:
        idx = data["daily"]["time"].index(date_str)

        return (
            f"Weather in {resolved_city.title()} on {date_str}: "
            f"Min {data['daily']['temperature_2m_min'][idx]}°C, "
            f"Max {data['daily']['temperature_2m_max'][idx]}°C, "
            f"Weather code {data['daily']['weathercode'][idx]}."
        )

    except Exception:
        return f"No forecast available for {resolved_city} on {date_str}"

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    print("REGISTERED TOOLS:", mcp.list_tools())

    mcp.run(
        transport=MCP_TRANSPORT,
        host=MCP_HOST,
        port=WEATHER_MCP_PORT
    )
