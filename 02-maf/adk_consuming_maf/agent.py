"""
Google ADK Agent Consuming Microsoft Agent Framework (MAF) A2A Agent

This example demonstrates cross-framework A2A communication:
- A Google ADK agent acts as the A2A client/orchestrator
- It connects to the MAF Weather Agent running on port 8002
- Combined with the local travel info, it provides comprehensive travel planning

Prerequisites:
1. Start the MAF Weather Agent:
   uvicorn "07-a2a-protocol.maf_agents.maf_weather_agent:app" --host localhost --port 8002

2. Set your GOOGLE_API_KEY for the ADK agent's LLM

3. Run this with adk web or the test script
"""

from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.genai import types


# ============================================================================
# Local Travel Planning Tools
# ============================================================================

DESTINATIONS = {
    "new york": {"country": "USA", "best_months": "Apr-Jun, Sep-Nov", "avg_temp_f": 55},
    "london": {"country": "UK", "best_months": "May-Sep", "avg_temp_f": 55},
    "tokyo": {"country": "Japan", "best_months": "Mar-May, Sep-Nov", "avg_temp_f": 60},
    "paris": {"country": "France", "best_months": "Apr-Jun, Sep-Nov", "avg_temp_f": 55},
    "sydney": {"country": "Australia", "best_months": "Sep-Nov, Mar-May", "avg_temp_f": 65},
}


def get_packing_suggestions(destination: str, trip_type: str = "vacation") -> dict:
    """
    Get packing suggestions for a destination.
    
    Args:
        destination: The city name
        trip_type: Type of trip (vacation, business, adventure)
    
    Returns:
        Packing suggestions based on destination
    """
    dest_lower = destination.lower().strip()
    
    base_items = ["Passport", "Phone charger", "Medications", "Travel insurance docs"]
    
    destination_items = {
        "new york": ["Walking shoes", "Layers for variable weather", "Metro card money"],
        "london": ["Umbrella", "Rain jacket", "Adapter plug (UK)"],
        "tokyo": ["Comfortable walking shoes", "Pocket WiFi reservation", "Cash (many places don't accept cards)"],
        "paris": ["Stylish casual clothes", "Good walking shoes", "French phrasebook"],
        "sydney": ["Sunscreen", "Swimwear", "Hat and sunglasses"],
    }
    
    trip_type_items = {
        "vacation": ["Camera", "Guidebook", "Snacks for the flight"],
        "business": ["Business cards", "Laptop", "Formal attire"],
        "adventure": ["First aid kit", "Water bottle", "Hiking boots"],
    }
    
    if dest_lower not in DESTINATIONS:
        return {
            "success": False,
            "message": f"Destination {destination} not found"
        }
    
    items = base_items + destination_items.get(dest_lower, []) + trip_type_items.get(trip_type.lower(), [])
    
    return {
        "success": True,
        "destination": destination.title(),
        "trip_type": trip_type,
        "packing_list": items,
        "message": f"Packing suggestions for {trip_type} trip to {destination.title()}"
    }


def get_best_travel_time(destination: str) -> dict:
    """
    Get the best time to visit a destination.
    
    Args:
        destination: The city name
    
    Returns:
        Information about the best time to visit
    """
    dest_lower = destination.lower().strip()
    
    if dest_lower not in DESTINATIONS:
        return {
            "success": False,
            "message": f"Destination {destination} not found. Available: {', '.join(d.title() for d in DESTINATIONS.keys())}"
        }
    
    info = DESTINATIONS[dest_lower]
    
    return {
        "success": True,
        "destination": destination.title(),
        "country": info["country"],
        "best_months": info["best_months"],
        "average_temperature_f": info["avg_temp_f"],
        "message": f"Best time to visit {destination.title()}: {info['best_months']}"
    }


def list_available_destinations() -> dict:
    """List all destinations this agent has information about."""
    return {
        "success": True,
        "destinations": [
            {"name": name.title(), "country": info["country"]}
            for name, info in DESTINATIONS.items()
        ],
        "message": f"Available destinations: {', '.join(d.title() for d in DESTINATIONS.keys())}"
    }


# ============================================================================
# Remote A2A Agent - MAF Weather Agent
# ============================================================================

# The MAF weather agent runs as a separate A2A server on port 8002
weather_agent = RemoteA2aAgent(
    name="weather_agent",
    description="""Remote weather agent (Microsoft Agent Framework via A2A protocol).
    Use this agent for:
    - Getting current weather conditions for cities
    - Getting weather forecasts (up to 7 days)
    - Checking weather alerts and warnings
    
    Supported cities: New York, London, Tokyo, Paris, Sydney
    """,
    agent_card=f"http://localhost:8002{AGENT_CARD_WELL_KNOWN_PATH}",
)


# ============================================================================
# Local Travel Planning Agent
# ============================================================================

travel_planning_agent = Agent(
    model="gemini-2.0-flash",
    name="travel_planning_agent",
    description="Local agent for travel planning - packing suggestions and best travel times.",
    instruction="""You are a travel planning specialist.

Your capabilities:
1. Suggest packing lists based on destination and trip type
2. Advise on the best time to visit destinations
3. List available destinations

Use the tools to provide helpful travel planning advice.""",
    tools=[get_packing_suggestions, get_best_travel_time, list_available_destinations],
)


# ============================================================================
# Root Agent - Travel Advisor with Weather Integration
# ============================================================================

root_agent = Agent(
    model="gemini-2.0-flash",
    name="travel_advisor",
    description="A comprehensive travel advisor that combines local planning with real-time weather data from a remote MAF agent.",
    instruction="""You are a comprehensive travel advisor that helps users plan their trips.

You have access to two specialized agents:
1. **travel_planning_agent** (local): For packing suggestions, best travel times, and destination info
2. **weather_agent** (remote via A2A to Microsoft Agent Framework): For current weather, forecasts, and alerts

When users ask about:
- Packing, what to bring → delegate to travel_planning_agent
- Best time to visit → delegate to travel_planning_agent  
- Current weather conditions → delegate to weather_agent
- Weather forecasts → delegate to weather_agent
- Weather alerts/warnings → delegate to weather_agent

For comprehensive trip planning:
1. Get travel timing advice from travel_planning_agent
2. Get current weather from weather_agent
3. Get packing suggestions from travel_planning_agent
4. Combine all information into helpful advice

Example workflow for "Help me plan a trip to Tokyo":
1. Ask travel_planning_agent about best time to visit
2. Ask weather_agent for current weather and forecast
3. Ask travel_planning_agent for packing suggestions
4. Synthesize into comprehensive advice

Always be friendly and provide context about the weather when recommending what to pack!
""",
    sub_agents=[travel_planning_agent, weather_agent],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
