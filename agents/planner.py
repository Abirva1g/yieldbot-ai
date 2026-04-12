"""Planner Agent - Main LangGraph workflow orchestration."""
import logging
from datetime import datetime
from typing import Annotated, List
from langgraph.graph import StateGraph, END
from agents.state import BotState, MarketData
from agents.analyzer import analyzer_agent
from agents.executor import executor_agent
from agents.monitor import monitor_agent
from config.settings import settings

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Main orchestrator for YieldBot AI workflow."""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(BotState)
        
        # Add nodes
        workflow.add_node("perceive", self.perceive)
        workflow.add_node("analyze", analyzer_agent.analyze_market_data)
        workflow.add_node("plan", self.create_plan)
        workflow.add_node("execute", executor_agent.execute_trade)
        workflow.add_node("monitor", monitor_agent.check_and_heal)
        
        # Set entry point
        workflow.set_entry_point("perceive")
        
        # Add edges
        workflow.add_edge("perceive", "analyze")
        workflow.add_edge("analyze", "plan")
        
        # Conditional edge: execute only if opportunities exist
        workflow.add_conditional_edges(
            "plan",
            self.should_execute,
            {
                "execute": "execute",
                "skip": "monitor"
            }
        )
        
        workflow.add_edge("execute", "monitor")
        
        # Loop back to perceive (unless paused)
        workflow.add_conditional_edges(
            "monitor",
            self.should_continue,
            {
                "continue": "perceive",
                "wait": "perceive"  # Still loop but with delay in main.py
            }
        )
        
        return workflow.compile()
    
    async def perceive(self, state: BotState) -> BotState:
        """Perceive market data from Jupiter API."""
        logger.info("Perceive: Fetching market data")
        
        iteration = state.get("iteration_count", 0) + 1
        state["iteration_count"] = iteration
        
        try:
            # In production, this would call JupiterService.get_quote()
            # For MVP, we simulate market data
            # Simulate slight price variation for testing
            base_price = 143.50  # SOL price
            variation = (iteration % 10 - 5) * 0.1  # -0.5 to +0.4
            
            market_data: MarketData = {
                "timestamp": datetime.utcnow(),
                "chain_id": 101,  # Solana devnet
                "token_pair": "SOL/USDC",
                "price": base_price + variation,
                "volume_24h": 1000000.0,
                "dex_liquidity": {"raydium": 500000, "orca": 300000}
            }
            
            state["market_data"] = market_data
            logger.info(f"Perceive: Fetched SOL/USDC price=${market_data['price']:.2f}")
            
        except Exception as e:
            logger.error(f"Perceive: Failed to fetch market data: {e}")
            # Keep existing market data if available
            if not state.get("market_data"):
                logger.warning("Perceive: No market data available")
        
        return state
    
    async def create_plan(self, state: BotState) -> BotState:
        """Create trading plan from opportunities."""
        logger.info("Plan: Creating trading plan")
        
        opportunities = state.get("opportunities", [])
        
        if not opportunities:
            logger.info("Plan: No opportunities to plan")
            state["selected_plan"] = None
            return state
        
        # Select best opportunity (lowest risk)
        best_opp = min(opportunities, key=lambda x: x["risk_score"])
        
        # Create simple plan for MVP
        state["selected_plan"] = {
            "opportunity_id": best_opp["id"],
            "actions": [{"type": "swap", "token_in": "USDC", "token_out": "SOL"}],
            "slippage_tolerance_bps": settings.executor.slippage_bps,
            "gas_budget_usd": 0.01,
            "confidence_score": 1.0 - best_opp["risk_score"]
        }
        
        logger.info(f"Plan: Created plan for opportunity {best_opp['id']}")
        return state
    
    def should_execute(self, state: BotState) -> str:
        """Determine if execution should proceed."""
        opportunities = state.get("opportunities", [])
        has_opportunities = len(opportunities) > 0
        
        # Also check if not in cooldown
        health_status = state.get("health_status", "healthy")
        if health_status == "paused":
            logger.info("Plan: Skipping execution - system paused")
            return "skip"
        
        if has_opportunities:
            logger.info(f"Plan: Executing - {len(opportunities)} opportunities found")
            return "execute"
        else:
            logger.info("Plan: Skipping execution - no opportunities")
            return "skip"
    
    def should_continue(self, state: BotState) -> str:
        """Determine if workflow should continue looping."""
        health_status = state.get("health_status", "healthy")
        
        if health_status == "paused":
            logger.info("Monitor: System paused, will wait before continuing")
            return "wait"
        
        logger.info("Monitor: Continuing loop")
        return "continue"
    
    async def run_iteration(self, state: BotState) -> BotState:
        """Run one complete iteration of the workflow."""
        return await self.graph.ainvoke(state)


# Global planner instance
planner = PlannerAgent()
