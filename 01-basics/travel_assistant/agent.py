"""
Travel Assistant Agent - Consumes Remote Currency Agent via A2A Protocol

This agent is a local travel assistant that:
1. Has a local tool for getting travel information
2. Consumes a remote Currency Agent via A2A for currency conversions

To run this example:
1. First, start the remote currency agent:
   uvicorn "07-a2a-protocol.remote_a2a.currency_agent.agent:a2a_app" --host localhost --port 8001

2. Then, run the travel assistant using adk web:
   adk web 07-a2a-protocol

Or run it programmatically using the test script.
"""

from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.genai import types

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Local Tools for the Travel Assistant
# ============================================================================

TRAVEL_DESTINATIONS = {
    "paris": {
        "country": "France",
        "currency": "EUR",
        "language": "French",
        "timezone": "CET (UTC+1)",
        "best_time": "April to June, September to November",
        "attractions": ["Eiffel Tower", "Louvre Museum", "Notre-Dame", "Champs-Élysées"],
        "avg_daily_budget": 150,  # in USD
        "description": "The City of Light, known for its art, fashion, gastronomy, and culture."
    },
    "tokyo": {
        "country": "Japan",
        "currency": "JPY",
        "language": "Japanese",
        "timezone": "JST (UTC+9)",
        "best_time": "March to May, September to November",
        "attractions": ["Tokyo Tower", "Senso-ji Temple", "Shibuya Crossing", "Mount Fuji day trip"],
        "avg_daily_budget": 120,  # in USD
        "description": "A fascinating blend of ultra-modern and traditional, with endless entertainment options."
    },
    "london": {
        "country": "United Kingdom",
        "currency": "GBP",
        "language": "English",
        "timezone": "GMT (UTC+0)",
        "best_time": "May to September",
        "attractions": ["Big Ben", "Tower of London", "British Museum", "Buckingham Palace"],
        "avg_daily_budget": 180,  # in USD
        "description": "A vibrant city rich in history, culture, and diverse neighborhoods."
    },
    "new york": {
        "country": "United States",
        "currency": "USD",
        "language": "English",
        "timezone": "EST (UTC-5)",
        "best_time": "April to June, September to November",
        "attractions": ["Statue of Liberty", "Central Park", "Times Square", "Empire State Building"],
        "avg_daily_budget": 200,  # in USD
        "description": "The city that never sleeps, offering world-class dining, shopping, and entertainment."
    },
    "sydney": {
        "country": "Australia",
        "currency": "AUD",
        "language": "English",
        "timezone": "AEST (UTC+10)",
        "best_time": "September to November, March to May",
        "attractions": ["Sydney Opera House", "Harbour Bridge", "Bondi Beach", "Taronga Zoo"],
        "avg_daily_budget": 160,  # in USD
        "description": "A stunning harbor city with beautiful beaches, iconic architecture, and laid-back vibes."
    },
    "mumbai": {
        "country": "India",
        "currency": "INR",
        "language": "Hindi, English",
        "timezone": "IST (UTC+5:30)",
        "best_time": "November to February",
        "attractions": ["Gateway of India", "Marine Drive", "Elephanta Caves", "Bollywood Studios"],
        "avg_daily_budget": 50,  # in USD
        "description": "India's financial capital, a city of dreams with rich cultural diversity."
    },
}


def get_destination_info(destination: str) -> dict:
    """
    Get travel information about a destination.
    
    Args:
        destination: The name of the city/destination to look up
    
    Returns:
        A dictionary with destination information
    """
    destination_lower = destination.lower().strip()
    
    if destination_lower in TRAVEL_DESTINATIONS:
        info = TRAVEL_DESTINATIONS[destination_lower]
        return {
            "success": True,
            "destination": destination.title(),
            **info,
            "message": f"Found information for {destination.title()}, {info['country']}"
        }
    
    available = list(TRAVEL_DESTINATIONS.keys())
    return {
        "success": False,
        "destination": destination,
        "message": f"Destination '{destination}' not found. Available destinations: {', '.join(d.title() for d in available)}"
    }


def calculate_trip_budget(destination: str, days: int) -> dict:
    """
    Calculate an estimated trip budget for a destination.
    
    Args:
        destination: The name of the city/destination
        days: Number of days for the trip
    
    Returns:
        A dictionary with the budget estimate in USD
    """
    destination_lower = destination.lower().strip()
    
    if destination_lower not in TRAVEL_DESTINATIONS:
        return {
            "success": False,
            "message": f"Destination '{destination}' not found."
        }
    
    info = TRAVEL_DESTINATIONS[destination_lower]
    daily_budget = info["avg_daily_budget"]
    
    # Budget breakdown
    accommodation = daily_budget * 0.4 * days
    food = daily_budget * 0.25 * days
    activities = daily_budget * 0.2 * days
    transport = daily_budget * 0.15 * days
    total = daily_budget * days
    
    return {
        "success": True,
        "destination": destination.title(),
        "days": days,
        "local_currency": info["currency"],
        "budget_usd": {
            "total": round(total, 2),
            "accommodation": round(accommodation, 2),
            "food": round(food, 2),
            "activities": round(activities, 2),
            "local_transport": round(transport, 2),
        },
        "daily_average_usd": daily_budget,
        "message": f"Estimated {days}-day trip budget for {destination.title()}: ${total} USD"
    }


def list_destinations() -> dict:
    """
    List all available travel destinations.
    
    Returns:
        A dictionary with the list of available destinations
    """
    destinations = []
    for name, info in TRAVEL_DESTINATIONS.items():
        destinations.append({
            "name": name.title(),
            "country": info["country"],
            "currency": info["currency"],
            "daily_budget_usd": info["avg_daily_budget"]
        })
    
    return {
        "success": True,
        "destinations": destinations,
        "message": f"Found {len(destinations)} available destinations"
    }


# ============================================================================
# Remote A2A Agent Configuration
# ============================================================================

# The currency_agent runs as a separate A2A server on port 8001
# We connect to it using RemoteA2aAgent
currency_agent = RemoteA2aAgent(
    name="currency_agent",
    description="""Remote agent specialized in currency conversions and exchange rates.
    Use this agent when you need to:
    - Convert amounts from one currency to another
    - Get current exchange rates between currencies
    - List supported currencies for conversion
    """,
    # The agent card URL tells this agent how to communicate with the remote agent
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)


# ============================================================================
# Local Travel Info Agent
# ============================================================================

travel_info_agent = Agent(
    model="gemini-2.0-flash",
    name="travel_info_agent",
    description="Local agent that provides travel destination information and budget calculations.",
    instruction="""You are a travel information specialist.

Your capabilities:
1. Get detailed information about travel destinations using get_destination_info
2. Calculate trip budgets using calculate_trip_budget  
3. List all available destinations using list_destinations

Always provide helpful and detailed travel information when asked.
""",
    tools=[get_destination_info, calculate_trip_budget, list_destinations],
)


# ============================================================================
# Root Agent (Travel Assistant)
# ============================================================================

root_agent = Agent(
    model="gemini-2.0-flash",
    name="travel_assistant",
    description="A comprehensive travel assistant that can provide destination information and handle currency conversions.",
    instruction="""You are a helpful travel assistant that helps users plan their trips.

You have access to two specialized agents:
1. **travel_info_agent** (local): For destination information, trip budgets, and travel tips
2. **currency_agent** (remote via A2A): For currency conversions and exchange rates

When a user asks about:
- Destination information, attractions, best time to visit → delegate to travel_info_agent
- Trip budget estimates → delegate to travel_info_agent, then optionally convert to local currency via currency_agent
- Currency conversions or exchange rates → delegate to currency_agent
- Combined queries (e.g., "How much is the Paris trip in Euros?") → coordinate between both agents

Workflow for budget with currency conversion:
1. First get the budget in USD from travel_info_agent
2. Then convert the USD amount to the destination's local currency using currency_agent
3. Present both values to the user

Always be friendly, informative, and provide context about your responses.
Format currency amounts clearly (e.g., $150 USD, €138 EUR).
""",
    sub_agents=[travel_info_agent, currency_agent],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
