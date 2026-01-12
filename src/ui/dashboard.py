import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

from main_graph import app
from src.quant_engine.greeks import calculate_greeks
from src.integration.kite_app import kite_client
from src.integration.yfinance_client import fetch_nifty_spot, fetch_india_vix

st.set_page_config(page_title="Agentic RAG Trader", layout="wide")

st.title("🤖 Hybrid Agentic RAG Trading System")

# Fetch initial spot & VIX for defaults
default_spot = fetch_nifty_spot()
if not default_spot: default_spot = 22000.0

default_iv = fetch_india_vix()
if not default_iv: default_iv = 15.0

# Sidebar Controls
st.sidebar.header("Simulation Controls")
mock_spot = st.sidebar.number_input("Spot Price", value=float(default_spot))
mock_iv = st.sidebar.number_input("IV (%)", value=float(default_iv))
mock_days = st.sidebar.slider("Days to Expiry", 1, 30, 5)

# Strategy Selector
strategy_mode = st.sidebar.selectbox(
    "Strategy Mode",
    options=["Auto (LLM)", "Short Strangle", "Short Straddle"],
    index=0
)

# Map selection to internal string
strategy_map = {
    "Auto (LLM)": None,
    "Short Strangle": "Short Strangle",
    "Short Straddle": "Short Straddle"
}
user_strategy = strategy_map[strategy_mode]

if st.sidebar.button("Run Agent Simulation"):
    with st.spinner("Agents are analyzing market data..."):
        # Construct Initial State
        initial_state = {
            "market_data": {
                "symbol": "NIFTY", 
                "spot_price": mock_spot, 
                "iv": mock_iv, 
                "days_to_expiry": mock_days
            },
            "user_selected_strategy": user_strategy
        }
        
        # Run Graph
        result = app.invoke(initial_state)
        
        # Store result in session state to persist across reruns
        st.session_state['result'] = result
        st.success("Simulation Complete!") # Added success message
        
# Display Results
if 'result' in st.session_state:
    result = st.session_state['result']
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Spot Price", result['market_data']['spot_price'])
    col2.metric("IV", f"{result['market_data']['iv']}%")
    col3.metric("Strategy", result['strategy_decision']['strategy'])
    col4.metric("Risk Status", result.get('risk_status', 'N/A'))

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Agent Reasoning", "Execution Plan", "Payoff Diagram"])
    
    with tab1:
        st.subheader("Strategist Agent")
        decision = result.get("strategy_decision", {})
        st.markdown(f"**Recommended Strategy:** `{decision.get('strategy')}`")
        if user_strategy:
             st.info(f"Manual Override Active: Selected {user_strategy}")
        
        st.markdown(f"**Rationale:** {decision.get('rationale')}")
        st.markdown(f"**LLM Analysis:**\n{decision.get('llm_analysis')}")
        
        with st.expander("View RAG Constraints"):
            st.write(decision.get("constraints"))
            
        st.subheader("Market Research Agent")
        st.write(result.get("research_data"))

    with tab2:
        st.subheader("Executor Agent")
        order = result.get("final_order", {})
        legs = order.get("legs", [])
        
        if not legs:
             st.error("No trades generated.")
        else:
             cols = st.columns(len(legs))
             greeks_data = []
             
             for i, leg in enumerate(legs):
                 with cols[i]:
                     st.write(f"**{leg['type']}**")
                     st.write(f"Strike: {leg['strike']}")
                     
                     # Calculate Greeks
                     # Retrieve Spot/IV/Time from market_data (or inputs if inputs changed)
                     # ideally usage consistent with the run input
                     m_data = result.get("market_data", {})
                     g = calculate_greeks(
                         m_data['spot_price'], 
                         leg['strike'], 
                         m_data['days_to_expiry'], 
                         m_data['iv'], 
                         leg['type']
                     )
                     greeks_data.append(g)
                     
                     st.dataframe(g)

             st.success(f"Risk Status: {result.get('risk_status')}")
             
             # Manual Execution Button
             if st.button("🚀 Execute Trade on Kite"):
                 if kite_client:
                      place_response = kite_client.place_order(order)
                      if "order_id" in place_response:
                           st.success(f"Order Placed! ID: {place_response['order_id']}")
                      else:
                           st.error(f"Failed to place order: {place_response}")
                 else:
                      st.warning("Kite Client not initialized. Check API Keys.")

    with tab3:
        st.subheader("Payoff Diagram")
        
        if legs:
            # Payoff Calculation
            spot_range = np.linspace(mock_spot * 0.9, mock_spot * 1.1, 100)
            pnl = np.zeros_like(spot_range)
            
            for leg in legs:
                strike = leg['strike']
                premium = 100 # Mock premium for visualization
                if leg['type'] == 'CE':
                    # Short Call Payoff
                    pnl += np.where(spot_range > strike, strike - spot_range, 0) + premium
                else:
                    # Short Put Payoff
                    pnl += np.where(spot_range < strike, spot_range - strike, 0) + premium
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=spot_range, y=pnl, mode='lines', name='P&L'))
            
            # Zero Line
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            # Current Spot Line
            fig.add_vline(x=mock_spot, line_dash="dash", line_color="blue", annotation_text="Spot")
            
            # Sigma Lines
            # Range Formula: Spot * (IV/100) * sqrt(Days/365)
            sigma_1 = mock_spot * (mock_iv / 100) * np.sqrt(mock_days / 365)
            
            fig.add_vline(x=mock_spot + sigma_1, line_dash="dot", line_color="green", annotation_text="+1σ")
            fig.add_vline(x=mock_spot - sigma_1, line_dash="dot", line_color="green", annotation_text="-1σ")
            
            fig.add_vline(x=mock_spot + 2*sigma_1, line_dash="dot", line_color="orange", annotation_text="+2σ")
            fig.add_vline(x=mock_spot - 2*sigma_1, line_dash="dot", line_color="orange", annotation_text="-2σ")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No legs to display payoff diagram.")
