import nsepython
import datetime

def fetch_option_chain(symbol="NIFTY"):
    """
    Fetches the live option chain for the given symbol (NIFTY/BANKNIFTY).
    Returns a cleaned dictionary focusing on the Current Expiry.
    """
    print(f"--- [Option Chain] Fetching data for {symbol} ---")
    try:
        # 1. Scraping raw JSON
        payload = nsepython.nse_optionchain_scrapper(symbol)
        
        if not payload or 'records' not in payload:
            print("Error: Empty payload from NSE.")
            return {}

        # 2. Identify Current Expiry
        expiry_dates = payload['records']['expiryDates']
        current_expiry = expiry_dates[0]
        print(f"Current Expiry: {current_expiry}")
        
        # 3. Extract relevant data
        data = payload['records']['data']
        spot_price = payload['records']['underlyingValue']
        
        # 4. Filter for Current Expiry and Near ATM (Spot +/- 2%)
        relevant_strikes = []
        min_strike = spot_price * 0.98
        max_strike = spot_price * 1.02
        
        for item in data:
            if item['expiryDate'] == current_expiry:
                strike = item['strikePrice']
                if min_strike <= strike <= max_strike:
                    processed_item = {
                        "strike": strike,
                        "ce_iv": item.get('CE', {}).get('impliedVolatility', 0),
                        "pe_iv": item.get('PE', {}).get('impliedVolatility', 0),
                        "ce_oi": item.get('CE', {}).get('openInterest', 0),
                        "pe_oi": item.get('PE', {}).get('openInterest', 0),
                        "ce_ltp": item.get('CE', {}).get('lastPrice', 0),
                        "pe_ltp": item.get('PE', {}).get('lastPrice', 0),
                    }
                    relevant_strikes.append(processed_item)
                    
        # Sort by strike
        relevant_strikes.sort(key=lambda x: x['strike'])
        
        return {
            "symbol": symbol,
            "expiry": current_expiry,
            "spot_price": spot_price,
            "chain": relevant_strikes
        }

    except Exception as e:
        print(f"Option Chain Fetch Failed: {e}")
        return {}

if __name__ == "__main__":
    # Test
    chain = fetch_option_chain()
    print(f"Fetched {len(chain.get('chain', []))} strikes.")
    if chain.get('chain'):
        print(chain['chain'][0])
