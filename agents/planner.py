"""Planner Agent - Orchestrates the full LangGraph workflow with real agents."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Annotated
from datetime import datetime
import logging
import random

from agents.state import BotState, MarketData, HealthStatus, reduce_opportunities, reduce_execution_history, reduce_price_history
from agents.analyzer import analyzer_agent
from agents.executor import executor_agent
from agents.monitor import monitor_agent
from config.settings import settings

logger = logging.getLogger(__name__)

# Экспорт для импорта в main.py
planner = None  # Будет установлен ниже после компиляции графа


# Build Graph с реальными агентами
workflow = StateGraph(BotState)

async def perceive_node(state: BotState) -> BotState:
    """Perceive: Get market data from Jupiter API or mock fallback."""
    logger.info("Perceive: Fetching market data...")
    
    # Check if we already have price history (don't overwrite it)
    existing_history = state.get("price_history", [])
    if existing_history:
        logger.info(f"Perceive: Using existing price history ({len(existing_history)} items)")
        # Just update with latest price if available
        if state.get("market_data"):
            logger.info(f"Perceive: Current price ${state['market_data']['price']:.2f}")
        return state
    
    try:
        # Try to get real data from Jupiter API
        from services.jupiter_service import jupiter_service
        
        # Get SOL/USDC price (main pair for MVP)
        market_data = await jupiter_service.get_token_price(
            input_mint="So11111111111111111111111111111111111111112",  # SOL
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            amount=1000000000  # 1 SOL in lamports
        )
        
        if market_data and market_data.get("price"):
            state["market_data"] = market_data
            
            # Update price history
            price_history = state.get("price_history", [])
            updated_history = price_history + [market_data]
            if len(updated_history) > 20:
                updated_history = updated_history[-20:]
            state["price_history"] = updated_history
            
            logger.info(f"Perceive: Got real price ${market_data['price']:.2f}")
            return state
    
    except Exception as e:
        logger.warning(f"Perceive: Failed to get real data: {e}")
    
    # Mock fallback for MVP when network is unavailable
    logger.warning("Perceive: Using mock data (network unavailable)")
    
    last_price = 143.50
    if state.get("price_history"):
        last_price = state["price_history"][-1].get("price", 143.50)
    
    # Simulate price movement with more volatility for testing
    new_price = last_price * (1 + random.uniform(-0.03, 0.03))
    
    mock_market_data: MarketData = {
        "timestamp": datetime.utcnow(),
        "chain_id": 101,  # Solana devnet
        "token_pair": "SOL/USDC",
        "price": new_price,
        "volume_24h": 1000000.0,
        "dex_liquidity": {"raydium": 500000, "orca": 300000}
    }
    
    state["market_data"] = mock_market_data
    
    # Update price history
    price_history = state.get("price_history", [])
    updated_history = price_history + [mock_market_data]
    if len(updated_history) > 20:
        updated_history = updated_history[-20:]
    state["price_history"] = updated_history
    
    logger.info(f"Perceive: Mock price ${new_price:.2f}")
    return state


async def analyze_node(state: BotState) -> BotState:
    """Analyze: Use real AnalyzerAgent to detect opportunities."""
    logger.info("Analyze: Starting market analysis...")
    
    # Call the real analyzer agent
    state = await analyzer_agent.analyze_market_data(state)
    
    opportunities = state.get("opportunities", [])
    if opportunities:
        logger.info(f"Analyze: Found {len(opportunities)} opportunity(s)")
        for opp in opportunities:
            logger.info(f"  - {opp['id']}: Return={opp['expected_return_bps']:.2f} bps, Risk={opp['risk_score']:.2f}")
    else:
        logger.info("Analyze: No opportunities detected")
    
    return state


async def execute_node(state: BotState) -> BotState:
    """Execute: Use real ExecutorAgent to execute trades."""
    logger.info("Execute: Starting trade execution...")
    
    opportunities = state.get("opportunities", [])
    if not opportunities:
        logger.info("Execute: No opportunities to execute, skipping")
        state["trade_result"] = None
        state["execution_metadata"] = {"reason": "no_opportunities"}
        return state
    
    # Call the real executor agent
    state = await executor_agent.execute_trade(state)
    
    trade_result = state.get("trade_result")
    if trade_result:
        status = "SUCCESS" if trade_result["success"] else "FAILED"
        logger.info(f"Execute: Trade {status}")
        if trade_result.get("tx_hash"):
            logger.info(f"Execute: TX Hash: {trade_result['tx_hash']}")
        if trade_result.get("error_message"):
            logger.error(f"Execute: Error: {trade_result['error_message']}")
    
    return state


async def monitor_node(state: BotState) -> BotState:
    """Monitor: Use real MonitorAgent for health checking and self-healing."""
    logger.info("Monitor: Checking health status...")
    
    # Call the real monitor agent
    state = await monitor_agent.check_and_heal(state)
    
    health_status = state.get("health_status", HealthStatus.HEALTHY)
    consecutive_failures = state.get("consecutive_failures", 0)
    
    logger.info(f"Monitor: Health={health_status}, ConsecutiveFailures={consecutive_failures}")
    
    # Update iteration count
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    
    return state


# Add nodes to graph
workflow.add_node("perceive", perceive_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("execute", execute_node)
workflow.add_node("monitor", monitor_node)

# Define edges
workflow.set_entry_point("perceive")
workflow.add_edge("perceive", "analyze")
workflow.add_edge("analyze", "execute")
workflow.add_edge("execute", "monitor")
# Graph executes once per invoke, no automatic loop back

# Compile the graph
app = workflow.compile()
planner = app  # Экспортируем как planner для совместимости с main.py

logger.info("Planner: Graph compiled successfully with real agents")
