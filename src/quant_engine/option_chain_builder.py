import pandas as pd
from datetime import datetime, timedelta
from src.integration.kite_app import kite_client

def get_option_chain_data(symbol="NIFTY", expiry_type="weekly"):
    """
    Builds an Option Chain using Kite Instruments.
    symbol: 'NIFTY' or 'BANKNIFTY'
    expiry_type: 'weekly' or 'monthly'
    """
    print(f"--- Building {symbol} {expiry_type} Option Chain ---")
    
    # 1. Fetch Instruments
    instruments = kite_client.get_instruments()
    if not instruments:
        print("Warning: No instruments fetched (Mock Mode). Returning mock chain.")
        # Return a mock DataFrame structure for simulation
        return pd.DataFrame([
            {"strike": 22000, "instrument_type": "CE", "tradingsymbol": "NIFTY24FEB22000CE", "instrument_token": 12345},
            {"strike": 22000, "instrument_type": "PE", "tradingsymbol": "NIFTY24FEB22000PE", "instrument_token": 12346},
        ])

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
