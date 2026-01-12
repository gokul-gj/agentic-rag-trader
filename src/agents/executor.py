from typing import Dict, Any
from src.integration.kite_app import kite_client
from src.quant_engine.sigma_calculator import get_strangle_strikes, get_atm_strike

def execute_order(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Executor Node.
    Takes the strategy decision and market data to generate final orders.
    """
    print("--- [Executor] Calculating Strikes ---")
    market_data = state.get("market_data", {})
    strategy_dec = state.get("strategy_decision", {})
    strategy_name = strategy_dec.get("strategy", "Short Strangle")
    
    if not market_data:
        return {"error": "No market data found"}
        
    spot = market_data.get("spot_price")
    iv = market_data.get("iv")
    days = market_data.get("days_to_expiry")
    sigma_mult = 1.0
    
    strikes = {}
    
    if strategy_name == "Short Straddle":
        atm = get_atm_strike(spot)
        strikes = {
            "sell_call_strike": atm,
            "sell_put_strike": atm,
            "type": "Straddle"
        }
    else:
        # Default Strangle
        strikes = get_strangle_strikes(spot, iv, days, sigma_mult)
    
    # Place Orders via Kite
    call_strike = strikes["sell_call_strike"]
    put_strike = strikes["sell_put_strike"]
    
    # Construct Symbols (Mock logic for symbol naming, in prod use option_chain_builder)
    # NIFTY 22 Feb 22400 CE -> NIFTY24FEB22400CE
    ce_symbol = f"NIFTY24FEB{call_strike}CE" 
    pe_symbol = f"NIFTY24FEB{put_strike}PE"
    
    print(f"--- [Executor] Generated Trade Plan: Sell {ce_symbol} and {pe_symbol} ---")
    
    # We DO NOT execute here anymore. We return the plan for user approval.
    
    order = {
        "action": "SELL",
        "strategy": "Short Strangle",
        "legs": [
            {
                "type": "CE",
                "strike": call_strike,
                "symbol": ce_symbol,
                "qty": 50,
                "order_id": None # To be filled after execution
            },
            {
                "type": "PE",
                "strike": put_strike,
                "symbol": pe_symbol,
                "qty": 50,
                "order_id": None
            }
        ],
        "analysis": strikes
    }
    
    return {"final_order": order}
