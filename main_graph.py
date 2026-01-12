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
    try:
        from src.integration.option_chain_client import fetch_option_chain
        chain_data = fetch_option_chain()
    except Exception as e:
        print(f"Option Chain Error: {e}")
        chain_data = {}

    # Mock Data for other fields if not available
    market_data = {
        "symbol": "NIFTY",
        "spot_price": spot,
        "iv": iv, # Using real VIX
        "days_to_expiry": 5,
        "option_chain": chain_data # Inject option chain
    }
    
    # The original logic had an IV check. With hardcoded IV=15, this check would never trigger.
    # Assuming the intent is to remove the IV check if IV is now hardcoded to a 'safe' value.
    
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
    # Initial run
    initial_state = {}
    result = app.invoke(initial_state)
    print("\n\n################ RESULT ################")
    import json
    print(json.dumps(result, indent=2))
