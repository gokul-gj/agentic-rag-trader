import pandas as pd
from datetime import datetime, timedelta
from src.integration.kite_app import kite_client

def get_option_chain_data(symbol="NIFTY", expiry_type="weekly"):
    """
    Builds an Option Chain using Kite Instruments.
    symbol: 'NIFTY' or 'BANKNIFTY'
    expiry_type: 'weekly' or 'monthly'
    Returns: DataFrame with option chain or raises exception if unavailable
    """
    print(f"--- Building {symbol} {expiry_type} Option Chain ---")
    
    # 1. Fetch Instruments
    instruments = kite_client.get_instruments()
    if not instruments:
        raise Exception(f"Failed to fetch instruments from Kite API. Cannot build option chain for {symbol}. Please check API connection.")

    # 2. Convert to DataFrame
    df = pd.DataFrame(instruments)
    
    # 3. Filter by Symbol
    df = df[df['name'] == symbol]
    
    # 4. Filter by Expiry
    # Logic to distinguish weekly vs monthly: 
    # Use 'expiry' column. Sort by date. Closest is current weekly/monthly.
    df['expiry'] = pd.to_datetime(df['expiry'])
    today = datetime.now()
    future_expiries = df[df['expiry'] >= today]['expiry'].unique()
    future_expiries.sort()
    
    if len(future_expiries) == 0:
        return pd.DataFrame()
        
    target_expiry = future_expiries[0] # Nearest expiry
    # If user wants monthly, logic would be slightly more complex (last Thursday of month)
    
    df_expiry = df[df['expiry'] == target_expiry]
    
    # 5. Filter Strikes (Optional optimization to reduce API calls)
    # For now, return the filtered DataFrame of instruments
    return df_expiry[['instrument_token', 'tradingsymbol', 'strike', 'instrument_type', 'expiry']]

def fetch_live_chain_snapshot(chain_df):
    """
    Takes the chain dataframe and fetches live quotes.
    """
    tokens = chain_df['instrument_token'].tolist()
    # Kite allows max 500 tokens maybe? Batching might be needed.
    quotes = kite_client.get_quote(tokens)
    
    return quotes

def get_expiry_date(chain_df):
    """
    Extracts the expiry date from option chain DataFrame.
    Returns: datetime object or None
    """
    if chain_df.empty:
        return None
    # All options in the chain should have same expiry
    return chain_df['expiry'].iloc[0]

def get_lot_size(symbol="NIFTY"):
    """
    Gets the lot size for the given symbol from Kite instruments.
    Returns: int (lot size) or raises exception
    """
    lot_sizes = {
        "NIFTY": 50,
        "BANKNIFTY": 15,
        "FINNIFTY": 40,
        "MIDCPNIFTY": 75
    }
    
    # Try to fetch from Kite API first
    try:
        instruments = kite_client.get_instruments()
        if instruments:
            df = pd.DataFrame(instruments)
            symbol_data = df[df['name'] == symbol]
            if not symbol_data.empty:
                # Get lot_size from first instrument
                lot_size = symbol_data['lot_size'].iloc[0]
                if lot_size:
                    return int(lot_size)
    except Exception as e:
        print(f"Could not fetch lot size from API: {e}")
    
    # Fallback to known values
    return lot_sizes.get(symbol, 50)

def find_closest_strike_in_chain(chain_df, target_strike, option_type="CE"):
    """
    Finds the closest available strike in the option chain.
    Args:
        chain_df: Option chain DataFrame
        target_strike: Desired strike price
        option_type: 'CE' or 'PE'
    Returns:
        Dict with strike info {'strike', 'tradingsymbol', 'instrument_token'}
    """
    # Filter by option type
    filtered = chain_df[chain_df['instrument_type'] == option_type].copy()
    
    if filtered.empty:
        raise Exception(f"No {option_type} options found in chain")
    
    # Find closest strike
    filtered['distance'] = abs(filtered['strike'] - target_strike)
    closest = filtered.nsmallest(1, 'distance').iloc[0]
    
    return {
        'strike': int(closest['strike']),
        'tradingsymbol': closest['tradingsymbol'],
        'instrument_token': closest['instrument_token']
    }

