"""
Microsoft Agent Framework (MAF) Agent Exposed via A2A Protocol

This example demonstrates how to expose a MAF agent as an A2A server
that can be consumed by Google ADK agents or any other A2A-compatible client.

The MAF Weather Agent provides:
- Current weather information (simulated)
- Weather forecasts
- Weather alerts

To run:
1. Install dependencies: pip install agent-framework --pre uvicorn fastapi

2. Start this MAF A2A server:
   uvicorn "07-a2a-protocol.maf_agents.maf_weather_agent:app" --host localhost --port 8002

3. The agent card will be available at:
   http://localhost:8002/.well-known/agent.json

4. Consume from ADK using RemoteA2aAgent pointing to http://localhost:8002
"""

import asyncio
from typing import Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Simulated weather data
WEATHER_DATA = {
    "new york": {
        "temperature": 72,
        "condition": "Partly Cloudy",
        "humidity": 65,
        "wind": "10 mph NW",
    },
    "london": {
        "temperature": 59,
        "condition": "Overcast",
        "humidity": 80,
        "wind": "15 mph SW",
    },
    "tokyo": {
        "temperature": 78,
        "condition": "Clear",
        "humidity": 55,
        "wind": "5 mph E",
    },
    "paris": {
        "temperature": 68,
        "condition": "Sunny",
        "humidity": 45,
        "wind": "8 mph N",
    },
    "sydney": {
        "temperature": 65,
        "condition": "Rainy",
        "humidity": 90,
        "wind": "20 mph SE",
    },
}


def get_current_weather(city: str) -> dict:
    """Get current weather for a city."""
    city_lower = city.lower().strip()
    if city_lower in WEATHER_DATA:
        data = WEATHER_DATA[city_lower]
        return {
            "success": True,
            "city": city.title(),
            "temperature_f": data["temperature"],
            "temperature_c": round((data["temperature"] - 32) * 5 / 9, 1),
            "condition": data["condition"],
            "humidity": f"{data['humidity']}%",
            "wind": data["wind"],
            "timestamp": datetime.now().isoformat(),
            "message": f"Current weather in {city.title()}: {data['temperature']}°F, {data['condition']}"
        }
    return {
        "success": False,
        "city": city,
        "message": f"Weather data not available for {city}. Available cities: {', '.join(c.title() for c in WEATHER_DATA.keys())}"
    }


def get_weather_forecast(city: str, days: int = 3) -> dict:
    """Get weather forecast for a city."""
    city_lower = city.lower().strip()
    if city_lower not in WEATHER_DATA:
        return {
            "success": False,
            "city": city,
            "message": f"Forecast not available for {city}"
        }
    
    base = WEATHER_DATA[city_lower]
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Clear"]
    
    forecast = []
    for i in range(days):
        date = datetime.now() + timedelta(days=i+1)
        temp_variation = (i * 3) % 10 - 5
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "day": date.strftime("%A"),
            "high_f": base["temperature"] + temp_variation + 5,
            "low_f": base["temperature"] + temp_variation - 10,
            "condition": conditions[(i + hash(city_lower)) % len(conditions)],
        })
    
    return {
        "success": True,
        "city": city.title(),
        "days": days,
        "forecast": forecast,
        "message": f"{days}-day forecast for {city.title()} generated"
    }


def get_weather_alerts(city: str) -> dict:
    """Get any active weather alerts for a city."""
    city_lower = city.lower().strip()
    
    # Simulated alerts
    alerts = {
        "sydney": [{"type": "Rain Warning", "severity": "Moderate", "message": "Heavy rain expected this afternoon"}],
        "london": [{"type": "Wind Advisory", "severity": "Low", "message": "Gusty winds possible tonight"}],
    }
    
    city_alerts = alerts.get(city_lower, [])
    
    return {
        "success": True,
        "city": city.title(),
        "alerts": city_alerts,
        "alert_count": len(city_alerts),
        "message": f"{len(city_alerts)} active alert(s) for {city.title()}" if city_alerts else f"No active alerts for {city.title()}"
    }


# Create FastAPI app for A2A protocol
app = FastAPI(title="MAF Weather Agent A2A Server")

# Agent Card - describes this agent's capabilities
AGENT_CARD = {
    "name": "weather_agent",
    "description": "A weather information agent that provides current conditions, forecasts, and weather alerts for major cities worldwide.",
    "url": "http://localhost:8002",
    "version": "1.0.0",
    "protocolVersion": "0.2.6",
    "capabilities": {},
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "skills": [
        {
            "id": "current_weather",
            "name": "Current Weather",
            "description": "Get current weather conditions for a city including temperature, humidity, and wind",
            "tags": ["weather", "current", "temperature"]
        },
        {
            "id": "weather_forecast", 
            "name": "Weather Forecast",
            "description": "Get multi-day weather forecast for a city",
            "tags": ["weather", "forecast", "prediction"]
        },
        {
            "id": "weather_alerts",
            "name": "Weather Alerts",
            "description": "Get active weather alerts and warnings for a city",
            "tags": ["weather", "alerts", "warnings"]
        }
    ]
}


@app.get("/.well-known/agent.json")
@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    """Return the A2A agent card describing this agent's capabilities."""
    return JSONResponse(content=AGENT_CARD)


@app.post("/")
@app.post("/a2a")
async def handle_a2a_request(request: Request):
    """
    Handle incoming A2A protocol requests.
    
    This is a simplified A2A handler that processes text messages
    and routes them to the appropriate weather functions.
    """
    try:
        body = await request.json()
        
        # Extract the message from A2A request format
        # A2A uses JSON-RPC 2.0 format
        method = body.get("method", "")
        params = body.get("params", {})
        request_id = body.get("id", "1")
        
        if method == "message/send":
            # Extract text from the message
            message = params.get("message", {})
            parts = message.get("parts", [])
            
            user_text = ""
            for part in parts:
                if part.get("kind") == "text":
                    user_text = part.get("text", "")
                    break
            
            # Process the message and generate response
            response_text = await process_weather_query(user_text)
            
            # Return A2A-formatted response
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "message": {
                        "role": "agent",
                        "parts": [{"kind": "text", "text": response_text}]
                    }
                }
            })
        
        elif method == "tasks/send":
            # Handle task-based requests
            task = params.get("task", {})
            message = task.get("message", {})
            parts = message.get("parts", [])
            
            user_text = ""
            for part in parts:
                if part.get("kind") == "text":
                    user_text = part.get("text", "")
                    break
            
            response_text = await process_weather_query(user_text)
            
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "id": f"task-{request_id}",
                    "status": {"state": "completed"},
                    "artifacts": [{
                        "parts": [{"kind": "text", "text": response_text}]
                    }]
                }
            })
        
        # Unknown method
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        })
        
    except Exception as e:
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": "error",
            "error": {"code": -32000, "message": str(e)}
        })


async def process_weather_query(query: str) -> str:
    """
    Process a natural language weather query and return a response.
    
    This is a simple keyword-based router. In production, you'd use
    an LLM or more sophisticated NLU.
    """
    query_lower = query.lower()
    
    # Extract city from query (simple heuristic)
    city = None
    for c in WEATHER_DATA.keys():
        if c in query_lower:
            city = c
            break
    
    if not city:
        # Try common city names that might be capitalized differently
        words = query.split()
        for word in words:
            if word.lower() in WEATHER_DATA:
                city = word.lower()
                break
    
    # Determine what type of weather info is requested
    if "forecast" in query_lower:
        if city:
            days = 3
            if "5" in query or "five" in query_lower:
                days = 5
            elif "7" in query or "week" in query_lower:
                days = 7
            result = get_weather_forecast(city, days)
            if result["success"]:
                forecast_lines = [f"{f['day']}: {f['condition']}, High: {f['high_f']}°F, Low: {f['low_f']}°F" 
                                  for f in result["forecast"]]
                return f"Weather forecast for {city.title()}:\n" + "\n".join(forecast_lines)
            return result["message"]
        return "Please specify a city for the forecast. Available cities: " + ", ".join(c.title() for c in WEATHER_DATA.keys())
    
    elif "alert" in query_lower or "warning" in query_lower:
        if city:
            result = get_weather_alerts(city)
            if result["alerts"]:
                alert_lines = [f"⚠️ {a['type']} ({a['severity']}): {a['message']}" for a in result["alerts"]]
                return f"Weather alerts for {city.title()}:\n" + "\n".join(alert_lines)
            return f"No active weather alerts for {city.title()}."
        return "Please specify a city to check for weather alerts."
    
    elif city or "weather" in query_lower or "temperature" in query_lower:
        if city:
            result = get_current_weather(city)
            if result["success"]:
                return (f"Current weather in {result['city']}:\n"
                        f"🌡️ Temperature: {result['temperature_f']}°F ({result['temperature_c']}°C)\n"
                        f"☁️ Condition: {result['condition']}\n"
                        f"💧 Humidity: {result['humidity']}\n"
                        f"💨 Wind: {result['wind']}")
            return result["message"]
        return "Please specify a city. Available cities: " + ", ".join(c.title() for c in WEATHER_DATA.keys())
    
    # Default response
    return (f"I'm a weather agent! I can help you with:\n"
            f"- Current weather conditions\n"
            f"- Weather forecasts (up to 7 days)\n"
            f"- Weather alerts and warnings\n\n"
            f"Available cities: {', '.join(c.title() for c in WEATHER_DATA.keys())}\n\n"
            f"Try asking: 'What's the weather in Tokyo?' or 'Get the forecast for London'")


if __name__ == "__main__":
    print("Starting MAF Weather Agent A2A Server...")
    print("Agent Card available at: http://localhost:8002/.well-known/agent.json")
    uvicorn.run(app, host="localhost", port=8002)
