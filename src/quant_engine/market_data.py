import random

def get_current_market_data():
    """
    Simulates fetching real-time market data.
    Returns a dictionary with Nifty Spot, IV, and DTE.
    """
    # In a real system, this would connect to a broker API
    return {
        "symbol": "NIFTY",
        "spot_price": 22000,   # As requested in the scenario
        "iv": 15,              # 15%
        "days_to_expiry": 5
    }
