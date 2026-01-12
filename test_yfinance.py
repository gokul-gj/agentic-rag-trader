import yfinance as yf
import pandas as pd

def test_yfinance():
    print("--- Testing Nifty 50 Spot (^NSEI) ---")
    nifty = yf.Ticker("^NSEI")
    try:
        hist = nifty.history(period="1d")
        if not hist.empty:
            print(f"Current Price: {hist['Close'].iloc[-1]}")
            print("Spot Data Fetch: SUCCESS")
        else:
            print("Spot Data Fetch: FAILED (Empty Data)")
    except Exception as e:
        print(f"Spot Data Fetch Error: {e}")

    print("\n--- Testing Nifty Option (Example Ticker) ---")
    # Ticker format for NSE Options on Yahoo is tricky or non-existent.
    # Often it doesn't work. Let's try a few formats if known, or skip.
    # Yahoo Finance usually doesn't stream NSE Options. 
    print("Skipping Options test as yfinance option chain support for NSE is unreliable.")

if __name__ == "__main__":
    test_yfinance()
