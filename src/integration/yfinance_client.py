import yfinance as yf

def fetch_nifty_spot():
    """
    Fetches the latest Nifty 50 Spot Price from Yahoo Finance.
    Returns:
        float: Latest Close/Price.
        None: If fetch fails.
    """
    try:
        nifty = yf.Ticker("^NSEI")
        # Get fast 1d history
        hist = nifty.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return round(price, 2)
    except Exception as e:
        print(f"Error fetching Nifty Spot from yfinance: {e}")
    
    return None

def fetch_india_vix():
    """
    Fetches the latest India VIX from Yahoo Finance (^INDIAVIX).
    Returns:
        float: Latest Close/Price.
        None: If fetch fails.
    """
    try:
        vix = yf.Ticker("^INDIAVIX")
        hist = vix.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return round(price, 2)
    except Exception as e:
        print(f"Error fetching India VIX from yfinance: {e}")
    
    return None
