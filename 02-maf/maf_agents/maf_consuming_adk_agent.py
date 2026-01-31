"""
Microsoft Agent Framework (MAF) Agent Consuming Google ADK A2A Agent

This example demonstrates cross-framework A2A communication:
- A Microsoft Agent Framework agent acts as the A2A client
- It connects to the Google ADK Currency Agent running on port 8001

Prerequisites:
1. Install Microsoft Agent Framework:
   pip install agent-framework --pre

2. Start the Google ADK Currency Agent (from the 07-a2a-protocol folder):
   uvicorn "07-a2a-protocol.remote_a2a.currency_agent.agent:a2a_app" --host localhost --port 8001

3. Set your Azure OpenAI or OpenAI credentials (for the MAF agent's LLM)

4. Run this script:
   python maf_consuming_adk_agent.py
"""

import asyncio
import os

import httpx
from a2a.client import A2ACardResolver
from agent_framework.a2a import A2AAgent


# Configuration
ADK_CURRENCY_AGENT_URL = os.getenv("ADK_CURRENCY_AGENT_URL", "http://localhost:8001")


async def demo_direct_a2a_client():
    """
    Demonstrates using Microsoft Agent Framework's A2AAgent to directly
    communicate with a Google ADK agent exposed via A2A.
    
    This is the simplest approach - just use MAF's A2AAgent as a client
    to call the remote ADK agent.
    """
    print("=" * 70)
    print("Demo 1: MAF A2AAgent as Direct Client to ADK Currency Agent")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        # Resolve the agent card from the ADK agent
        resolver = A2ACardResolver(
            httpx_client=http_client,
            base_url=ADK_CURRENCY_AGENT_URL
        )
        
        try:
            agent_card = await resolver.get_agent_card()
            print(f"\n✅ Connected to ADK Agent: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
            
            # Create MAF A2A agent wrapper
            a2a_agent = A2AAgent(
                name=agent_card.name,
                description=agent_card.description,
                agent_card=agent_card,
                url=ADK_CURRENCY_AGENT_URL,
            )
            
            # Test queries to the ADK Currency Agent
            test_queries = [
                "What is the exchange rate from USD to EUR?",
                "Convert 500 USD to Japanese Yen",
                "List all supported currencies",
            ]
            
            for query in test_queries:
                print(f"\n📤 Query: {query}")
                print("-" * 50)
                
                response = await a2a_agent.run(query)
                
                print("📥 Response from ADK Agent:")
                for message in response.messages:
                    print(f"   {message.text}")
                    
        except Exception as e:
            print(f"\n❌ Error connecting to ADK agent: {e}")
            print("   Make sure the ADK Currency Agent is running on port 8001")
            print("   Run: uvicorn '07-a2a-protocol.remote_a2a.currency_agent.agent:a2a_app' --host localhost --port 8001")
            return


async def demo_maf_orchestrator_with_a2a():
    """
    Demonstrates a MAF agent that orchestrates between local tools and 
    a remote ADK agent via A2A.
    
    This shows how to build a MAF agent that:
    1. Has its own local capabilities (travel planning)
    2. Delegates currency operations to the remote ADK agent via A2A
    """
    print("\n" + "=" * 70)
    print("Demo 2: MAF Orchestrator with Remote ADK A2A Agent")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        # First, connect to the ADK Currency Agent
        resolver = A2ACardResolver(
            httpx_client=http_client,
            base_url=ADK_CURRENCY_AGENT_URL
        )
        
        try:
            agent_card = await resolver.get_agent_card()
            print(f"\n✅ Connected to remote currency agent: {agent_card.name}")
            
            # Create A2A agent wrapper for the remote currency agent
            currency_a2a_agent = A2AAgent(
                name="currency_converter",
                description="Remote agent for currency conversions (via A2A protocol to ADK agent)",
                agent_card=agent_card,
                url=ADK_CURRENCY_AGENT_URL,
            )
            
            # Define local travel planning functions
            def get_travel_budget_usd(destination: str, days: int) -> str:
                """Get estimated travel budget in USD for a destination."""
                budgets = {
                    "paris": 150,
                    "tokyo": 120,
                    "london": 180,
                    "new york": 200,
                    "sydney": 160,
                }
                dest_lower = destination.lower()
                if dest_lower in budgets:
                    daily = budgets[dest_lower]
                    total = daily * days
                    return f"Estimated budget for {days} days in {destination}: ${total} USD (${daily}/day)"
                return f"Budget information not available for {destination}"
            
            def get_destination_info(destination: str) -> str:
                """Get basic information about a travel destination."""
                info = {
                    "paris": "Paris, France - Currency: EUR, Language: French, Best time: Apr-Jun, Sep-Nov",
                    "tokyo": "Tokyo, Japan - Currency: JPY, Language: Japanese, Best time: Mar-May, Sep-Nov", 
                    "london": "London, UK - Currency: GBP, Language: English, Best time: May-Sep",
                }
                dest_lower = destination.lower()
                if dest_lower in info:
                    return info[dest_lower]
                return f"Information not available for {destination}"
            
            # Test local function
            test_destination = "Tokyo"
            test_days = 5
            print(f"\n📤 Local Query: Budget for {test_days} days in {test_destination}")
            print("-" * 50)
            
            budget_result = get_travel_budget_usd(test_destination, test_days)
            print(f"📥 Local Budget Tool Response:")
            print(f"   {budget_result}")
            
            dest_info = get_destination_info(test_destination)
            print(f"📥 Local Destination Info:")
            print(f"   {dest_info}")
            
            # Now use the A2A agent for currency conversion
            print(f"\n📤 Now asking remote ADK agent for currency conversion...")
            print("-" * 50)
            
            a2a_response = await currency_a2a_agent.run("Convert 600 USD to Japanese Yen")
            print("📥 Response from ADK Currency Agent (via A2A):")
            for msg in a2a_response.messages:
                print(f"   {msg.text}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("Microsoft Agent Framework ↔ Google ADK A2A Communication Demo")
    print("=" * 70)
    print(f"\nTarget ADK Agent URL: {ADK_CURRENCY_AGENT_URL}")
    
    # Demo 1: Direct A2A client
    await demo_direct_a2a_client()
    
    # Demo 2: MAF orchestrator with A2A
    await demo_maf_orchestrator_with_a2a()
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
