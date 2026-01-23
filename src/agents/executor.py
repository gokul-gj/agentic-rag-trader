from typing import Dict, Any
from src.integration.kite_app import kite_client
from src.quant_engine.sigma_calculator import get_strangle_strikes, get_atm_strike
from src.quant_engine.option_chain_builder import get_lot_size

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
    symbol = market_data.get("symbol", "NIFTY")
    option_chain = market_data.get("option_chain")
    
    # Get sigma multiplier from strategy decision (LLM recommendation)
    sigma_mult = strategy_dec.get("recommended_sigma", 1.0)
    
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
    
    # Get real option symbols from option chain
    try:
        if option_chain is not None and not option_chain.empty:
            # Option chain DataFrame has columns: strike, tradingsymbol_ce, tradingsymbol_pe, etc.
            available_strikes = option_chain['strike'].tolist()
            
            # Find closest strike for Call
            ce_strike = min(available_strikes, key=lambda x: abs(x - call_strike))
            # Find closest strike for Put  
            pe_strike = min(available_strikes, key=lambda x: abs(x - put_strike))
            
            # Get the actual trading symbols from Kite data
            ce_row = option_chain[option_chain['strike'] == ce_strike]
            pe_row = option_chain[option_chain['strike'] == pe_strike]
            
            if not ce_row.empty and ce_row['tradingsymbol_ce'].iloc[0]:
                ce_symbol = ce_row['tradingsymbol_ce'].iloc[0]
            else:
                raise Exception(f"No CE option found for strike {ce_strike}")
                
            if not pe_row.empty and pe_row['tradingsymbol_pe'].iloc[0]:
                pe_symbol = pe_row['tradingsymbol_pe'].iloc[0]
            else:
                raise Exception(f"No PE option found for strike {pe_strike}")
            
            call_strike = ce_strike  # Use actual strike from chain
            put_strike = pe_strike  # Use actual strike from chain
            
            print(f"✅ Found options: {ce_symbol} and {pe_symbol}")
        else:
            raise Exception("Option chain data not available")
    except Exception as e:
        print(f"Error getting option symbols from chain: {e}")
        raise Exception(f"Cannot execute order without valid option chain data: {e}")
    
    # Get dynamic lot size
    lot_size = get_lot_size(symbol)
    
    print(f"--- [Executor] Generated Trade Plan: Sell {ce_symbol} and {pe_symbol} ---")
    
    # We DO NOT execute here anymore. We return the plan for user approval.
    
    order = {
        "action": "ADJUST" if state.get("adjustment_needed") else "OPEN",
        "strategy": strategy_name,
        "legs": [],
        "analysis": strikes
    }

    # If adjustment needed, close existing position first (Mock logic for demo)
    if state.get("adjustment_needed"):
        print("--- [Executor] Generating CLOSE orders for existing position ---")
        # In real system, fetch actual open positions here
        # For demo, we close a hypothetical previous position
        order["legs"].extend([
            {
                "type": "CE",
                "strike": call_strike, # Assuming we are rolling same strikes for simplicity in demo
                "instrument": "EXISTING_CE",
                "quantity": lot_size,
                "action": "BUY", # Close Short
                "order_id": "CLOSE_LEG_1"
            },
            {
                "type": "PE",
                "strike": put_strike,
                "instrument": "EXISTING_PE",
                "quantity": lot_size,
                "action": "BUY", # Close Short
                "order_id": "CLOSE_LEG_2"
            }
        ])

    # Add New Opening Legs
    order["legs"].extend([
            {
                "type": "CE",
                "strike": call_strike,
                "instrument": ce_symbol,
                "quantity": lot_size,
                "action": "SELL",
                "order_id": None
            },
            {
                "type": "PE",
                "strike": put_strike,
                "instrument": pe_symbol,
                "quantity": lot_size,
                "action": "SELL",
                "order_id": None
            }
    ])
    
    return {"final_order": order}
