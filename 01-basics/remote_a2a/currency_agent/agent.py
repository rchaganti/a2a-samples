"""
Remote Currency Agent - Exposed via A2A Protocol

This agent provides currency conversion functionality and can be consumed
by other agents via the A2A (Agent-to-Agent) protocol.

To run this agent as an A2A server:
    uvicorn 07-a2a-protocol.remote_a2a.currency_agent.agent:a2a_app --host localhost --port 8001

Or using adk api_server:
    adk api_server --a2a --port 8001 07-a2a-protocol/remote_a2a
"""

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from dotenv import load_dotenv

load_dotenv()

# Simulated exchange rates (in production, use a real API)
EXCHANGE_RATES = {
    ("USD", "EUR"): 0.92,
    ("USD", "GBP"): 0.79,
    ("USD", "JPY"): 149.50,
    ("USD", "CAD"): 1.36,
    ("USD", "AUD"): 1.53,
    ("USD", "INR"): 83.12,
    ("USD", "CHF"): 0.88,
    ("USD", "CNY"): 7.24,
    ("USD", "MXN"): 17.15,
    ("USD", "BRL"): 4.97,
    ("EUR", "USD"): 1.09,
    ("EUR", "GBP"): 0.86,
    ("EUR", "JPY"): 162.85,
    ("GBP", "USD"): 1.27,
    ("GBP", "EUR"): 1.16,
    ("JPY", "USD"): 0.0067,
    ("INR", "USD"): 0.012,
}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: The amount to convert
        from_currency: The source currency code (e.g., 'USD', 'EUR')
        to_currency: The target currency code (e.g., 'GBP', 'JPY')
    
    Returns:
        A dictionary with the conversion result
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency == to_currency:
        return {
            "success": True,
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": amount,
            "exchange_rate": 1.0,
            "message": f"{amount} {from_currency} = {amount} {to_currency}"
        }
    
    # Direct conversion
    rate_key = (from_currency, to_currency)
    if rate_key in EXCHANGE_RATES:
        rate = EXCHANGE_RATES[rate_key]
        converted = round(amount * rate, 2)
        return {
            "success": True,
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": converted,
            "exchange_rate": rate,
            "message": f"{amount} {from_currency} = {converted} {to_currency}"
        }
    
    # Try conversion through USD as intermediate
    if from_currency != "USD" and to_currency != "USD":
        from_to_usd = (from_currency, "USD")
        usd_to_target = ("USD", to_currency)
        
        if from_to_usd in EXCHANGE_RATES and usd_to_target in EXCHANGE_RATES:
            rate1 = EXCHANGE_RATES[from_to_usd]
            rate2 = EXCHANGE_RATES[usd_to_target]
            combined_rate = rate1 * rate2
            converted = round(amount * combined_rate, 2)
            return {
                "success": True,
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": converted,
                "exchange_rate": round(combined_rate, 4),
                "message": f"{amount} {from_currency} = {converted} {to_currency} (via USD)"
            }
    
    return {
        "success": False,
        "original_amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "converted_amount": None,
        "exchange_rate": None,
        "message": f"Exchange rate not available for {from_currency} to {to_currency}"
    }


def get_exchange_rate(from_currency: str, to_currency: str) -> dict:
    """
    Get the current exchange rate between two currencies.
    
    Args:
        from_currency: The source currency code (e.g., 'USD', 'EUR')
        to_currency: The target currency code (e.g., 'GBP', 'JPY')
    
    Returns:
        A dictionary with the exchange rate information
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency == to_currency:
        return {
            "success": True,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": 1.0,
            "message": f"1 {from_currency} = 1 {to_currency}"
        }
    
    rate_key = (from_currency, to_currency)
    if rate_key in EXCHANGE_RATES:
        rate = EXCHANGE_RATES[rate_key]
        return {
            "success": True,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": rate,
            "message": f"1 {from_currency} = {rate} {to_currency}"
        }
    
    return {
        "success": False,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "exchange_rate": None,
        "message": f"Exchange rate not available for {from_currency} to {to_currency}"
    }


def list_supported_currencies() -> dict:
    """
    List all supported currencies for conversion.
    
    Returns:
        A dictionary with the list of supported currency codes
    """
    currencies = set()
    for from_curr, to_curr in EXCHANGE_RATES.keys():
        currencies.add(from_curr)
        currencies.add(to_curr)
    
    currency_names = {
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
        "JPY": "Japanese Yen",
        "CAD": "Canadian Dollar",
        "AUD": "Australian Dollar",
        "INR": "Indian Rupee",
        "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan",
        "MXN": "Mexican Peso",
        "BRL": "Brazilian Real",
    }
    
    return {
        "success": True,
        "currencies": [
            {"code": code, "name": currency_names.get(code, code)}
            for code in sorted(currencies)
        ],
        "message": f"Supported currencies: {', '.join(sorted(currencies))}"
    }


# Define the Currency Agent
root_agent = Agent(
    model="gemini-2.0-flash",
    name="currency_agent",
    description="A currency conversion agent that can convert amounts between different currencies and provide exchange rate information.",
    instruction="""You are a helpful currency conversion assistant.

Your capabilities:
1. Convert amounts from one currency to another using the convert_currency tool
2. Get exchange rates between currencies using the get_exchange_rate tool  
3. List all supported currencies using the list_supported_currencies tool

When users ask about currency conversions:
- Always confirm the currencies and amount before converting
- Provide clear, formatted results
- If a currency is not supported, let the user know and suggest alternatives

Supported currency codes include: USD, EUR, GBP, JPY, CAD, AUD, INR, CHF, CNY, MXN, BRL

Always be helpful and provide context about the conversions when appropriate.
""",
    tools=[convert_currency, get_exchange_rate, list_supported_currencies],
)

# Create the A2A application
# This makes the agent accessible via the A2A protocol
a2a_app = to_a2a(root_agent, port=8001)
