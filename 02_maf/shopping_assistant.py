
import asyncio
import os
from typing import Optional

import httpx
from a2a.client import A2ACardResolver
from agent_framework.a2a import A2AAgent

# ADK A2A Agent Configuration
ADK_CURRENCY_AGENT_URL = os.getenv("ADK_CURRENCY_AGENT_URL", "http://localhost:8001")

PRODUCTS = {
    "laptop": {"price": 1299.99, "category": "Electronics"},
    "headphones": {"price": 199.99, "category": "Electronics"},
    "keyboard": {"price": 89.99, "category": "Electronics"},
    "mouse": {"price": 49.99, "category": "Electronics"},
    "monitor": {"price": 449.99, "category": "Electronics"},
    "backpack": {"price": 79.99, "category": "Accessories"},
    "water bottle": {"price": 24.99, "category": "Accessories"},
    "notebook": {"price": 12.99, "category": "Office"},
    "pen set": {"price": 19.99, "category": "Office"},
    "desk lamp": {"price": 59.99, "category": "Office"},
}

def get_product_price(product_name: str) -> dict:
    """
    Get the price of a product in USD.
    
    Args:
        product_name: Name of the product to look up
    
    Returns:
        Product information including price in USD
    """
    product_lower = product_name.lower().strip()
    
    if product_lower in PRODUCTS:
        product = PRODUCTS[product_lower]
        return {
            "success": True,
            "product": product_name.title(),
            "price_usd": product["price"],
            "category": product["category"],
            "message": f"{product_name.title()}: ${product['price']:.2f} USD"
        }
    
    available = list(PRODUCTS.keys())
    return {
        "success": False,
        "product": product_name,
        "message": f"Product '{product_name}' not found. Available products: {', '.join(p.title() for p in available)}"
    }

def calculate_cart_total(items: list[dict]) -> dict:
    """
    Calculate the total price for a shopping cart.
    
    Args:
        items: List of items with 'product' and 'quantity' keys
    
    Returns:
        Cart total and breakdown in USD
    """
    cart_items = []
    subtotal = 0.0
    
    for item in items:
        product_name = item.get("product", "").lower().strip()
        quantity = item.get("quantity", 1)
        
        if product_name in PRODUCTS:
            product = PRODUCTS[product_name]
            item_total = product["price"] * quantity
            subtotal += item_total
            cart_items.append({
                "product": product_name.title(),
                "unit_price": product["price"],
                "quantity": quantity,
                "item_total": round(item_total, 2)
            })
        else:
            cart_items.append({
                "product": product_name.title(),
                "error": "Product not found"
            })
    
    # Apply tax (8.5%)
    tax_rate = 0.085
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    return {
        "success": True,
        "items": cart_items,
        "subtotal_usd": round(subtotal, 2),
        "tax_rate": f"{tax_rate * 100}%",
        "tax_usd": tax,
        "total_usd": total,
        "message": f"Cart total: ${total:.2f} USD (including ${tax:.2f} tax)"
    }

def list_products(category: Optional[str] = None) -> dict:
    """
    List available products, optionally filtered by category.
    
    Args:
        category: Optional category to filter by (Electronics, Accessories, Office)
    
    Returns:
        List of available products
    """
    if category:
        category_lower = category.lower().strip()
        filtered = {
            name: info for name, info in PRODUCTS.items()
            if info["category"].lower() == category_lower
        }
        
        if not filtered:
            categories = list(set(p["category"] for p in PRODUCTS.values()))
            return {
                "success": False,
                "message": f"Category '{category}' not found. Available categories: {', '.join(categories)}"
            }
        
        products = filtered
    else:
        products = PRODUCTS
    
    product_list = [
        {
            "name": name.title(),
            "price_usd": info["price"],
            "category": info["category"]
        }
        for name, info in products.items()
    ]
    
    return {
        "success": True,
        "products": product_list,
        "count": len(product_list),
        "message": f"Found {len(product_list)} products" + (f" in {category}" if category else "")
    }


async def demo_maf_with_a2a_currency():
    """
    Demonstrates a MAF shopping assistant that uses the remote ADK
    Currency Agent via A2A for currency conversions.
    """
    print("=" * 70)
    print("MAF Shopping Assistant with Remote ADK Currency Agent (A2A)")
    print("=" * 70)
    print(f"\nConnecting to ADK Currency Agent at: {ADK_CURRENCY_AGENT_URL}")
    
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
            
            # Create MAF A2A agent wrapper for the remote currency agent
            currency_agent = A2AAgent(
                name="currency_converter",
                description="""Remote agent specialized in currency conversions and exchange rates.
                Use this agent when you need to:
                - Convert amounts from one currency to another
                - Get current exchange rates between currencies
                - List supported currencies for conversion
                """,
                agent_card=agent_card,
                url=ADK_CURRENCY_AGENT_URL,
            )
            
            # Run interactive demo scenarios
            await run_demo_scenarios(currency_agent)
                    
        except Exception as e:
            print(f"\n❌ Error connecting to ADK agent: {e}")
            print("   Make sure the ADK Currency Agent is running on port 8001")
            print("   Run: uvicorn '01-basics.remote_a2a.currency_agent.agent:a2a_app' --host localhost --port 8001")
            import traceback
            traceback.print_exc()

async def run_demo_scenarios(currency_agent: A2AAgent):
    """Run demonstration scenarios showing local tools + remote A2A agent."""
    
    # Scenario 1: Simple currency query (direct A2A call)
    print("\n" + "-" * 70)
    print("Scenario 1: Direct Currency Query via A2A")
    print("-" * 70)
    
    query = "What is the exchange rate from USD to EUR?"
    print(f"\n📤 Query: {query}")
    
    response = await currency_agent.run(query)
    print("📥 Response from ADK Currency Agent:")
    for message in response.messages:
        print(f"   {message.text}")
    
    # Scenario 2: Currency conversion (direct A2A call)
    print("\n" + "-" * 70)
    print("Scenario 2: Currency Conversion via A2A")
    print("-" * 70)
    
    query = "Convert 500 USD to Japanese Yen"
    print(f"\n📤 Query: {query}")
    
    response = await currency_agent.run(query)
    print("📥 Response from ADK Currency Agent:")
    for message in response.messages:
        print(f"   {message.text}")
    
    # Scenario 3: List supported currencies (direct A2A call)
    print("\n" + "-" * 70)
    print("Scenario 3: List Supported Currencies via A2A")
    print("-" * 70)
    
    query = "List all supported currencies"
    print(f"\n📤 Query: {query}")
    
    response = await currency_agent.run(query)
    print("📥 Response from ADK Currency Agent:")
    for message in response.messages:
        print(f"   {message.text}")
    
    # Scenario 4: Combined - Local shopping + Remote currency conversion
    print("\n" + "-" * 70)
    print("Scenario 4: Local Shopping Tools + Remote Currency Conversion")
    print("-" * 70)
    
    # First, use local tools to get product prices and calculate cart
    print("\n📦 Step 1: Using LOCAL shopping tools...")
    
    # Get laptop price
    laptop_result = get_product_price("laptop")
    print(f"   Product lookup: {laptop_result['message']}")
    
    # Get headphones price
    headphones_result = get_product_price("headphones")
    print(f"   Product lookup: {headphones_result['message']}")
    
    # Calculate cart total
    cart_result = calculate_cart_total([
        {"product": "laptop", "quantity": 1},
        {"product": "headphones", "quantity": 2}
    ])
    print(f"   Cart total: {cart_result['message']}")
    
    # Now convert the total to Euros using the remote A2A agent
    print("\n🌐 Step 2: Using REMOTE A2A agent for currency conversion...")
    
    total_usd = cart_result["total_usd"]
    query = f"Convert {total_usd} USD to EUR"
    print(f"   Query to ADK Currency Agent: {query}")
    
    response = await currency_agent.run(query)
    print("   Response from ADK Currency Agent:")
    for message in response.messages:
        print(f"      {message.text}")
    
    # Scenario 5: Convert to multiple currencies
    print("\n" + "-" * 70)
    print("Scenario 5: Convert Shopping Cart to Multiple Currencies")
    print("-" * 70)
    
    print(f"\n💰 Shopping cart total: ${total_usd} USD")
    print("   Converting to multiple currencies via A2A...")
    
    currencies = ["EUR", "GBP", "JPY", "CAD"]
    for currency in currencies:
        query = f"Convert {total_usd} USD to {currency}"
        response = await currency_agent.run(query)
        for message in response.messages:
            # Extract just the conversion result
            if message.text:
                print(f"   → {currency}: {message.text}")

async def interactive_mode(currency_agent: A2AAgent):
    """Run an interactive session where users can enter queries."""
    
    print("\n" + "=" * 70)
    print("Interactive Mode")
    print("=" * 70)
    print("\nYou can now enter queries. Type 'quit' to exit.")
    print("Examples:")
    print("  - 'list products' (local)")
    print("  - 'price of laptop' (local)")
    print("  - 'cart: laptop x1, headphones x2' (local)")
    print("  - 'convert 100 USD to EUR' (remote A2A)")
    print("  - 'exchange rate USD to GBP' (remote A2A)")
    
    while True:
        try:
            user_input = input("\n🛒 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Simple routing based on keywords
            input_lower = user_input.lower()
            
            if 'list products' in input_lower or 'show products' in input_lower:
                category = None
                for cat in ['electronics', 'accessories', 'office']:
                    if cat in input_lower:
                        category = cat
                        break
                result = list_products(category)
                print(f"📦 {result['message']}")
                if result['success']:
                    for p in result['products']:
                        print(f"   - {p['name']}: ${p['price_usd']:.2f} ({p['category']})")
            
            elif 'price' in input_lower:
                # Extract product name
                for product in PRODUCTS.keys():
                    if product in input_lower:
                        result = get_product_price(product)
                        print(f"📦 {result['message']}")
                        break
                else:
                    print("📦 Please specify a product name")
            
            elif 'cart' in input_lower:
                # Parse cart items from input like "cart: laptop x1, headphones x2"
                # This is a simplified parser
                items = []
                for product in PRODUCTS.keys():
                    if product in input_lower:
                        # Try to find quantity
                        import re
                        pattern = rf'{product}\s*x?\s*(\d+)?'
                        match = re.search(pattern, input_lower)
                        qty = int(match.group(1)) if match and match.group(1) else 1
                        items.append({"product": product, "quantity": qty})
                
                if items:
                    result = calculate_cart_total(items)
                    print(f"🛒 {result['message']}")
                    for item in result['items']:
                        if 'error' not in item:
                            print(f"   - {item['product']} x{item['quantity']}: ${item['item_total']:.2f}")
                else:
                    print("🛒 Please specify products for your cart")
            
            elif any(word in input_lower for word in ['convert', 'exchange', 'currency', 'rate', 'usd', 'eur', 'gbp', 'jpy']):
                # Currency-related query - delegate to remote A2A agent
                print("🌐 Asking remote ADK Currency Agent...")
                response = await currency_agent.run(user_input)
                for message in response.messages:
                    print(f"💱 {message.text}")
            
            else:
                print("❓ I can help with:")
                print("   - Product prices and shopping cart calculations (local)")
                print("   - Currency conversions and exchange rates (via A2A)")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("Microsoft Agent Framework ↔ Google ADK A2A Demo")
    print("Shopping Assistant consuming Currency Agent via A2A Protocol")
    print("=" * 70)
    
    # Run the demo scenarios
    await demo_maf_with_a2a_currency()
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nThis example demonstrated:")
    print("  1. Direct A2A queries to the remote ADK Currency Agent")
    print("  2. Local shopping tools (product prices, cart calculation)")
    print("  3. Combined workflow: local tools + remote A2A agent")
    print("\nThe MAF agent successfully communicated with the ADK agent")
    print("via the A2A protocol - proving framework interoperability!")


if __name__ == "__main__":
    asyncio.run(main())
