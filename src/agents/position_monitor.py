import csv
import os
from typing import Dict, Any
from src.integration.llm_client import query_llm
import json

LOG_FILE = os.path.join(os.getcwd(), 'data', 'market_history', 'option_chain_log.csv')

def monitor_positions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Position Monitor Node.
    Checks if existing positions need adjustment using LLM analysis.
    """
    print("--- [Position Monitor] Checking Active Positions with LLM ---")
    
    # In a real system, we'd read the actual open order book from Kite.
    # Here we mock reading the last "logged" trade from CSV if available.
    
    last_trade_context = "No active positions found in log."
    entry_price = 0
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_trade_context = lines[-1].strip() # Simple mock: just take last line
                    # Mock parsing (assuming CSV structure isn't strict for this demo)
                    # Real impl would parse CSV properly
        except Exception as e:
            print(f"Error reading log: {e}")

    market_data = state.get("market_data", {})
    current_spot = market_data.get("spot_price", 22000)
    current_iv = market_data.get("iv", 12)
    research_summary = state.get("research_data", "No news.")

    # Construct Prompt
    system_prompt = (
        "You are a Portfolio Manager. Monitor the following position. "
        "Decide if we need to ADJUST (Roll/Hedge) or HOLD based on market conditions. "
        "Rules: "
        "1. If Spot Price has moved significantly (>2%) from Entry, consider Adjustment. "
        "2. If News is 'Bearish' and we are Short Puts, consider Exit. "
        "3. Otherwise, recommend HOLD to collect Theta. "
        "Output JSON: {'decision': 'HOLD', 'ADJUST', or 'EXIT', 'reason': '...'}"
    )
    
    user_prompt = f"""
    Current Market:
    - Spot: {current_spot}
    - IV: {current_iv}
    - News: {research_summary}
    
    Position Info:
    {last_trade_context}
    
    Decision?
    """
    
    try:
        llm_response = query_llm(system_prompt, user_prompt)
        print(f"Position Monitor Thoughts: {llm_response}")
        
        # Simple parsing
        adjustment_needed = False
        if "adjust" in llm_response.lower() or "exit" in llm_response.lower():
            adjustment_needed = True
            
        return {
            "adjustment_needed": adjustment_needed,
            "monitor_analysis": llm_response
        }
        
    except Exception as e:
        print(f"Position Monitor LLM Failed: {e}")
        return {"adjustment_needed": False}
