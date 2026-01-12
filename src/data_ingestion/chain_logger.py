import csv
import os
import datetime
import random

# For this mock, we will generate synthetic option chain data
# similar to what we might get from an API (e.g., NSE Python)

LOG_DIR = os.path.join(os.getcwd(), 'data', 'market_history')
CSV_FILE = os.path.join(LOG_DIR, 'option_chain_log.csv')

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def get_mock_option_chain():
    """Generates a mock snapshot of an option chain."""
    spot = 22000 + random.randint(-50, 50)
    strikes = [21900, 21950, 22000, 22050, 22100]
    
    chain_data = []
    
    timestamp = datetime.datetime.now().isoformat()
    
    for strike in strikes:
        # Mocking Call (CE) and Put (PE) data
        ce_price = max(0.05, (spot - strike) + random.randint(10, 30)) if spot > strike else random.randint(10, 50)
        pe_price = max(0.05, (strike - spot) + random.randint(10, 30)) if spot < strike else random.randint(10, 50)
        
        ce_iv = 15 + random.uniform(-1, 1)
        pe_iv = 16 + random.uniform(-1, 1)
        
        row = {
            "timestamp": timestamp,
            "spot": spot,
            "strike": strike,
            "ce_last_price": round(ce_price, 2),
            "pe_last_price": round(pe_price, 2),
            "ce_iv": round(ce_iv, 2),
            "pe_iv": round(pe_iv, 2)
        }
        chain_data.append(row)
        
    return chain_data

def log_chain_snapshot():
    """Fetches data and appends to CSV."""
    ensure_log_dir()
    
    data = get_mock_option_chain()
    
    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerows(data)
        
    print(f"Logged {len(data)} rows to {CSV_FILE}")

if __name__ == "__main__":
    log_chain_snapshot()
