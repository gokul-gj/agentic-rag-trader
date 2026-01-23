import math

def calculate_range(spot: float, iv: float, days_to_expiry: int) -> float:
    """
    Calculates the expected range based on IV and time.
    Formula: Spot * (IV / 100) * sqrt(Days / 365)
    """
    return spot * (iv / 100) * math.sqrt(days_to_expiry / 365)

def round_to_nearest(value: float, base: int = 50) -> int:
    """Rounds a value to the nearest base (e.g., 50 for Nifty)."""
    return int(base * round(value / base))

def get_strangle_strikes(spot: float, iv: float, days: int, sigma_mult: float = 1.0) -> dict:
    """
    Calculates the Short Strangle strikes based on Sigma range.
    Args:
        spot: Current spot price.
        iv: Implied Volatility (annualized percent).
        days: Days to expiry.
        sigma_mult: Multiplier for the range (e.g., 1.0 for 1-SD).
    Returns:
        Dictionary with 'call_strike', 'put_strike', and 'range'.
    """
    market_range = calculate_range(spot, iv, days)
    adjustment = market_range * sigma_mult
    
    upper_bound = spot + adjustment
    lower_bound = spot - adjustment
    
    call_strike = round_to_nearest(upper_bound)
    put_strike = round_to_nearest(lower_bound)
    
    return {
        "range_points": round(market_range, 2),
        "sigma_mult": sigma_mult,
        "upper_bound_raw": round(upper_bound, 2),
        "lower_bound_raw": round(lower_bound, 2),
        "sell_call_strike": call_strike,
        "sell_put_strike": put_strike
    }

def get_atm_strike(spot: float) -> int:
    """Returns the At-The-Money (ATM) strike."""
    return round_to_nearest(spot)

def find_closest_available_strike(target_strike: float, available_strikes: list, base: int = 50) -> int:
    """
    Finds the closest available strike from a list of available strikes.
    Args:
        target_strike: Calculated ideal strike
        available_strikes: List of actual strikes available in option chain
        base: Strike interval (50 for Nifty, 100 for BankNifty)
    Returns:
        Closest available strike
    """
    if not available_strikes:
        # Fallback to rounding if no chain available
        return round_to_nearest(target_strike, base)
    
    # Find closest strike in available list
    closest = min(available_strikes, key=lambda x: abs(x - target_strike))
    return int(closest)
