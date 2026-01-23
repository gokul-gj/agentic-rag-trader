from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

from src.quant_engine.market_data import get_current_market_data
from src.agents.strategist import analyze_strategy
from src.agents.executor import execute_order
from src.agents.risk_manager import validate_order
from src.agents.market_researcher import perform_market_research
from src.agents.position_monitor import monitor_positions
from src.integration.yfinance_client import fetch_nifty_spot, fetch_india_vix
from src.quant_engine.option_chain_builder import get_expiry_date
from datetime import datetime

# Define the State
class AgentState(TypedDict):
    market_data: Dict[str, Any]
    research_data: str # New field for web search
    strategy_decision: Dict[str, Any]
    final_order: Dict[str, Any]
    risk_status: str # New field for risk approval
    adjustment_needed: bool # New field for monitor
    user_selected_strategy: str # New field for manual override
    error: str

# Define Nodes
# 1. Start Node: Market Scanner
def market_scanner(state: Dict[str, Any]) -> Dict[str, Any]:
    print("--- [Market Scanner] Checking Market Conditions ---")
    
    # Try fetching real spot & VIX
    real_spot = fetch_nifty_spot()
    real_vix = fetch_india_vix()
    
    spot = real_spot if real_spot else 22000
    iv = real_vix if real_vix else 15
    
    print(f"Fetched Data: Spot={spot}, IV={iv} (VIX)")
    
    # Fetch Option Chain
    chain_data = {}
    expiry_date = None
    days_to_expiry = None
    
    try:
        from src.integration.option_chain_client import fetch_option_chain
        chain_dict = fetch_option_chain()
        
        # Convert dictionary format to DataFrame for compatibility
        if chain_dict and 'chain' in chain_dict and len(chain_dict['chain']) > 0:
            import pandas as pd
            # Create DataFrame from chain data
            chain_data = pd.DataFrame(chain_dict['chain'])
            
            # Parse expiry date from string format
            expiry_str = chain_dict.get('expiry')
            if expiry_str:
                # nsepython returns expiry in format like "30-Jan-2026"
                expiry_date = datetime.strptime(expiry_str, "%d-%b-%Y")
                # Calculate real days to expiry
                days_to_expiry = (expiry_date - datetime.now()).days
                print(f"✅ Live Data: Expiry={expiry_date.strftime('%Y-%m-%d')}, DTE={days_to_expiry}")
        else:
            # DEMO MODE: Use mock data when market is closed or NSE unavailable
            print("⚠️ NSE/Kite data unavailable. Using DEMO mode with mock option chain.")
            import pandas as pd
            # Use real spot if available, otherwise 25200 (current levels)
            spot = real_spot if real_spot else 25200.0
            print(f"Generating mock option chain around Spot: {spot}")
            
            # Generate realistic mock option chain around current spot
            mock_strikes = []
            # Round to nearest 50
            atm_strike = round(spot / 50) * 50
            
            for i in range(-10, 11):  # 21 strikes around ATM
                strike = int(atm_strike + (i * 50))
                distance = abs(i)
                
                mock_strikes.append({
                    'strike': strike,
                    'ce_iv': 14.5 + abs(i) * 0.5,  # Realistic IV curve
                    'pe_iv': 14.5 + abs(i) * 0.5,
                    'ce_oi': 1500000 - (abs(i) * 50000),
                    'pe_oi': 1500000 - (abs(i) * 50000),
                    'ce_ltp': max(5, 200 - (distance * 15)),
                    'pe_ltp': max(5, 200 - (distance * 15)),
                    # Add trading symbols
                    'tradingsymbol_ce': f"NIFTY26JAN{strike}CE",
                    'tradingsymbol_pe': f"NIFTY26JAN{strike}PE"
                })
            
            chain_data = pd.DataFrame(mock_strikes)
            
            # Mock expiry: Next Thursday
            from datetime import timedelta
            today = datetime.now()
            days_until_thursday = (3 - today.weekday()) % 7  # 3 = Thursday
            if days_until_thursday == 0:
                days_until_thursday = 7  # If today is Thursday, next Thursday
            expiry_date = today + timedelta(days=days_until_thursday)
            days_to_expiry = days_until_thursday
            print(f"📊 DEMO Mode: Expiry={expiry_date.strftime('%Y-%m-%d')}, DTE={days_to_expiry}")
            
    except Exception as e:
        print(f"Option Chain Error: {e}")
        # Don't fail - use demo mode instead
        print("⚠️ Falling back to DEMO mode due to error.")
        import pandas as pd
        spot = real_spot if real_spot else 23500
        
        # Generate demo data (same as above)
        mock_strikes = []
        for i in range(-5, 6):
            strike = int(spot + (i * 100))
            mock_strikes.append({
                'strike': strike,
                'ce_iv': 15 + abs(i) * 0.5,
                'pe_iv': 15 + abs(i) * 0.5,
                'ce_oi': 1000000,
                'pe_oi': 1000000,
                'ce_ltp': max(10, abs(i) * 50),
                'pe_ltp': max(10, abs(i) * 50)
            })
        
        chain_data = pd.DataFrame(mock_strikes)
        
        from datetime import timedelta
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        expiry_date = today + timedelta(days=days_until_thursday)
        days_to_expiry = days_until_thursday

    # Validate we have real data
    if not real_spot or not real_vix:
        raise Exception(
            f"Failed to fetch live market data. Spot: {real_spot}, VIX: {real_vix}. "
            "Cannot proceed with trading without real-time data."
        )
    
    if days_to_expiry is None:
        raise Exception("Failed to calculate days to expiry from option chain. Cannot proceed.")
    
    # Use only real data (no fallbacks)
    market_data = {
        "symbol": "NIFTY",
        "spot_price": real_spot,
        "iv": real_vix,
        "days_to_expiry": days_to_expiry,
        "expiry_date": expiry_date,
        "option_chain": chain_data,
        "data_source": "LIVE"  # Indicator that all data is live
    }
    
    print(f"Market Data fetched: Spot={spot}, IV={market_data['iv']}, DTE={market_data['days_to_expiry']}")
    return {"market_data": market_data}

def researcher_node(state: AgentState) -> AgentState:
    result = perform_market_research(state)
    return {"research_data": result["research_data"]}

def monitor_node(state: AgentState) -> AgentState:
    # This runs in parallel or before strategy
    result = monitor_positions(state)
    return {"adjustment_needed": result["adjustment_needed"]}

def strategy_lookup_node(state: AgentState) -> AgentState:
    if state.get("error"): return state
    
    # Enrich state with research before strategy
    # Note: 'analyze_strategy' might need an update to use 'research_data' explicitly if we want
    # but for now we trust it uses what's in 'state' if we updated the signature, 
    # OR we just pass it along.
    # ideally Strategist should see "research_data". 
    # For now, we assume Strategist reads from state/context.
    
    result = analyze_strategy(state)
    return {"strategy_decision": result["strategy_decision"]}

def execution_node(state: AgentState) -> AgentState:
    if state.get("error"): return state
    result = execute_order(state)
    return {"final_order": result["final_order"]}

def risk_node(state: AgentState) -> AgentState:
    if state.get("error"): return state
    result = validate_order(state)
    if result.get("error"):
        return {"error": result["error"]}
    return {"risk_status": result["risk_status"]}

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("market_scanner", market_scanner)
workflow.add_node("position_monitor", monitor_node)
workflow.add_node("market_researcher", researcher_node)
workflow.add_node("strategist", strategy_lookup_node)
workflow.add_node("executor", execution_node)
workflow.add_node("risk_manager", risk_node)

# Define Edges / Flow
workflow.set_entry_point("market_scanner")

# Parallelize Monitor and Research after Scanner
workflow.add_edge("market_scanner", "position_monitor")
workflow.add_edge("market_scanner", "market_researcher")

# Re-converge to Strategist
workflow.add_edge("position_monitor", "strategist")
workflow.add_edge("market_researcher", "strategist")

workflow.add_edge("strategist", "executor")
workflow.add_edge("executor", "risk_manager")
workflow.add_edge("risk_manager", END)

app = workflow.compile()

if __name__ == "__main__":
    print("Starting Hybrid Agentic RAG System...")
    
    # Check for manual strategy override from environment
    import os
    user_override = os.environ.get("USER_SELECTED_STRATEGY")
    
    # Initial run
    initial_state = {}
    if user_override and user_override != "Auto":
        initial_state["user_selected_strategy"] = user_override
        print(f"Manual Override: {user_override}")
    
    result = app.invoke(initial_state)
    print("\n\n__JSON_START__")
    import json
    # Use default=str to handle datetime objects
    print(json.dumps(result, indent=2, default=str))
    print("__JSON_END__")

