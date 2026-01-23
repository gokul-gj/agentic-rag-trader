import datetime
import pandas as pd
import yfinance as yf

def fetch_option_chain(symbol="NIFTY"):
    """
    Fetches option chain data using yfinance.
    For NIFTY, uses ^NSEI ticker.
    Returns a cleaned dictionary with option chain data.
    """
    print(f"--- [Option Chain] Fetching data for {symbol} via yfinance ---")
    
    try:
        # Map symbols to Yahoo Finance tickers
        ticker_map = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK"
        }
        
        ticker_symbol = ticker_map.get(symbol, "^NSEI")
        ticker = yf.Ticker(ticker_symbol)
        
        # Get option expiration dates
        expirations = ticker.options
        
        if not expirations or len(expirations) == 0:
            print("⚠️ No option data available from yfinance. Falling back to SIMULATED/MOCK data.")
            mock_data = generate_mock_chain(symbol)
            mock_data["is_simulated"] = True
            mock_data["warning"] = "Data is SIMULATED. Do not use for real trading."
            return mock_data
        
        # Use the first (nearest) expiration
        expiry_date_str = expirations[0]
        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d")
        current_expiry = expiry_date.strftime("%d-%b-%Y")
        
        print(f"Expiry Date: {current_expiry}")
        
        # Get option chain for this expiry
        opt_chain = ticker.option_chain(expiry_date_str)
        calls = opt_chain.calls
        puts = opt_chain.puts
        
        # Get current spot price
        spot_price = ticker.history(period="1d")['Close'].iloc[-1] if len(ticker.history(period="1d")) > 0 else 23500
        print(f"Spot Price: {spot_price:.2f}")
        
        # Merge calls and puts on strike
        strikes_data = []
        
        # Get unique strikes from both calls and puts
        all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
        
        for strike in all_strikes:
            # Get CE data
            ce_data = calls[calls['strike'] == strike]
            pe_data = puts[puts['strike'] == strike]
            
            # Generate trading symbols
            expiry_str = expiry_date.strftime("%d%b%y").upper()
            ce_symbol = f"{symbol}{expiry_str}{int(strike)}CE"
            pe_symbol = f"{symbol}{expiry_str}{int(strike)}PE"
            
            strike_info = {
                'strike': strike,
                'tradingsymbol_ce': ce_symbol,
                'tradingsymbol_pe': pe_symbol,
                'ce_iv': ce_data['impliedVolatility'].iloc[0] * 100 if not ce_data.empty and 'impliedVolatility' in ce_data.columns else 15.0,
                'pe_iv': pe_data['impliedVolatility'].iloc[0] * 100 if not pe_data.empty and 'impliedVolatility' in pe_data.columns else 15.0,
                'ce_oi': ce_data['openInterest'].iloc[0] if not ce_data.empty and 'openInterest' in ce_data.columns else 0,
                'pe_oi': pe_data['openInterest'].iloc[0] if not pe_data.empty and 'openInterest' in pe_data.columns else 0,
                'ce_ltp': ce_data['lastPrice'].iloc[0] if not ce_data.empty and 'lastPrice' in ce_data.columns else 0,
                'pe_ltp': pe_data['lastPrice'].iloc[0] if not pe_data.empty and 'lastPrice' in pe_data.columns else 0,
            }
            strikes_data.append(strike_info)
        
        print(f"✅ Fetched {len(strikes_data)} strikes from yfinance")
        
        return {
            "symbol": symbol,
            "expiry": current_expiry,
        }
        
    except Exception as e:
        print(f"yfinance fetch failed: {e}")
        print("⚠️ Falling back to generated option chain data")
        # Try to get spot from yfinance even if options fail
        try:
            ticker = yf.Ticker(ticker_map.get(symbol, "^NSEI"))
            spot_price = ticker.history(period="1d")['Close'].iloc[-1]
            print(f"Got live spot for mock generation: {spot_price}")
        except:
            spot_price = None
            
        return generate_mock_chain(symbol, spot_price)

import math
from scipy.stats import norm

def black_scholes_price(S, K, T, r, sigma, option_type="CE"):
    """
    Calculate Option Price using Black-Scholes model
    S: Spot Price
    K: Strike Price
    T: Time to Expiry (in years)
    r: Risk-free rate (decimal)
    sigma: Volatility (decimal)
    """
    d1 = (math.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    if option_type == "CE":
        price = S * norm.cdf(d1) - K * math.exp(-r*T) * norm.cdf(d2)
    else:
        price = K * math.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
    return max(0.05, price) # Minimum tick size

def generate_mock_chain(symbol="NIFTY", spot_price=None):
    """
    Generates realistic mock option chain data using Black-Scholes pricing.
    Uses live spot price and live VIX if available.
    """
    # 1. Get Live Spot Price
    if spot_price is None:
        try:
            ticker = yf.Ticker("^NSEI")
            spot_price = ticker.history(period="1d")['Close'].iloc[-1]
            print(f"Got live spot for simulation: {spot_price}")
        except:
            spot_price = 25200.0 # Fallback
            
    # 2. Get Live VIX (Volatility)
    try:
        vix_ticker = yf.Ticker("^INDIAVIX")
        vix = vix_ticker.history(period="1d")['Close'].iloc[-1]
        print(f"Got live VIX for simulation: {vix}")
    except:
        vix = 13.5 # Fallback average VIX
        
    print(f"--- [Mock Chain] Generating strikes around Spot: {spot_price:.2f} with VIX: {vix:.2f} ---")
    
    # Calculate next Thursday expiry
    today = datetime.datetime.now()
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0:
        days_until_thursday = 7
    expiry_date = today + datetime.timedelta(days=days_until_thursday)
    current_expiry = expiry_date.strftime("%d-%b-%Y")
    
    # Time to expiry in years
    days_to_expiry_val = max(1, days_until_thursday)
    T = days_to_expiry_val / 365.0
    r = 0.07 # Risk free rate 7%
    sigma = vix / 100.0 # Volatility from VIX
    
    strikes_data = []
    # Round spot to nearest 50 for ATM strike
    atm_strike = round(spot_price / 50) * 50
    
    # Generate wider range of strikes: ATM +/- 1000 points
    for i in range(-20, 21):
        strike = atm_strike + (i * 50)
        
        # Calculate realistic option premiums using Black-Scholes
        ce_premium = black_scholes_price(spot_price, strike, T, r, sigma, "CE")
        pe_premium = black_scholes_price(spot_price, strike, T, r, sigma, "PE")
        
        expiry_str = expiry_date.strftime("%d%b%y").upper()
        ce_symbol = f"{symbol}{expiry_str}{int(strike)}CE"
        pe_symbol = f"{symbol}{expiry_str}{int(strike)}PE"
        
        # IV Skew: OTM Puts have higher IV (Smile/Smirk)
        iv_skew = 0.0
        if strike < spot_price: # OTM Puts / ITM Calls
             iv_skew = (spot_price - strike) / spot_price * 20 # Skew
        
        strike_data = {
            'strike': strike,
            'tradingsymbol_ce': ce_symbol,
            'tradingsymbol_pe': pe_symbol,
            'ce_iv': vix + (0.5 if strike > spot_price else 0), 
            'pe_iv': vix + iv_skew,
            'ce_oi': int(1000000 * math.exp(-0.0001 * abs(strike - spot_price))), # Gauss distro OI
            'pe_oi': int(1000000 * math.exp(-0.0001 * abs(strike - spot_price))),
            'ce_ltp': round(ce_premium, 2),
            'pe_ltp': round(pe_premium, 2),
        }
        strikes_data.append(strike_data)
    
    print(f"✅ Generated {len(strikes_data)} strikes pricing via Black-Scholes")
    
    return {
        "symbol": symbol,
        "expiry": current_expiry,
        "spot_price": spot_price,
        "chain": strikes_data
    }

if __name__ == "__main__":
    chain = fetch_option_chain()
    print(f"\n✅ Fetched {len(chain.get('chain', []))} strikes")
    if chain.get('chain'):
        print(f"Spot: {chain.get('spot_price', 'N/A')}")
        print("\nSample strikes:")
        for strike in chain['chain'][8:11]:
            print(f"  {strike['strike']}: CE={strike['tradingsymbol_ce']}, PE={strike['tradingsymbol_pe']}")
