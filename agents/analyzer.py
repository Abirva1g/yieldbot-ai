"""Analyzer Agent for detecting yield opportunities."""
import logging
from datetime import datetime
from typing import List, Optional
from agents.state import BotState, MarketData, Opportunity, HealthStatus
from config.settings import settings

logger = logging.getLogger(__name__)


def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average."""
    if not prices:
        return 0.0
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema


def calculate_risk_score(
    price_impact_bps: float,
    num_hops: int,
    deviation_bps: float,
    max_hops: int = 2,
    max_deviation_bps: int = 500
) -> float:
    """Calculate risk score based on multiple factors."""
    # Price impact penalty (0-30 points)
    price_impact_penalty = min(price_impact_bps / 10, 30)
    
    # Route complexity penalty (0-40 points)
    if num_hops > max_hops:
        route_complexity_penalty = 40
    else:
        route_complexity_penalty = (num_hops / max_hops) * 20
    
    # Deviation magnitude penalty (0-30 points)
    if deviation_bps > max_deviation_bps:
        deviation_penalty = 30  # Suspicious
    else:
        deviation_penalty = (deviation_bps / max_deviation_bps) * 30
    
    # Weighted sum
    risk_score = (
        price_impact_penalty * 0.3 +
        route_complexity_penalty * 0.4 +
        deviation_penalty * 0.3
    ) / 100.0
    
    return min(risk_score, 1.0)


async def analyze_market_data(state: BotState) -> BotState:
    """Analyze market data and detect opportunities."""
    logger.info("Analyze: Starting market analysis")
    
    market_data = state.get("market_data")
    if not market_data:
        logger.warning("Analyze: No market data available")
        state["opportunities"] = []
        state["analysis_metadata"] = {"ema": 0, "deviation_bps": 0}
        return state
    
    current_price = market_data["price"]
    price_history = state.get("price_history", [])
    
    # Update price history
    updated_history = price_history + [market_data]
    if len(updated_history) > 20:
        updated_history = updated_history[-20:]
    state["price_history"] = updated_history
    
    # Calculate EMA
    prices = [md["price"] for md in updated_history]
    ema_period = settings.analyzer.ema_period
    ema = calculate_ema(prices, ema_period)
    
    # Calculate deviation
    if ema > 0:
        deviation_bps = ((current_price - ema) / ema) * 10000
    else:
        deviation_bps = 0
    
    logger.info(f"Analyze: Current price={current_price}, EMA={ema:.2f}, Deviation={deviation_bps:.2f} bps")
    
    # Check for opportunities
    opportunities = []
    min_threshold = settings.analyzer.min_profit_threshold_bps
    
    if abs(deviation_bps) > min_threshold:
        # Create opportunity
        risk_score = calculate_risk_score(
            price_impact_bps=abs(deviation_bps) * 0.1,  # Estimated impact
            num_hops=1,  # Default for MVP
            deviation_bps=abs(deviation_bps),
            max_hops=settings.analyzer.max_hops,
            max_deviation_bps=settings.analyzer.max_deviation_bps
        )
        
        opportunity: Opportunity = {
            "id": f"opp_{datetime.utcnow().timestamp()}",
            "type": "arbitrage",
            "chain_from": 101,  # Solana devnet
            "chain_to": 101,
            "expected_return_bps": abs(deviation_bps),
            "risk_score": risk_score,
            "required_capital_usd": 100.0,  # Default for MVP
            "expiry_block": 0  # Will be set by executor
        }
        
        opportunities.append(opportunity)
        logger.info(f"Analyze: Opportunity detected! Return={abs(deviation_bps):.2f} bps, Risk={risk_score:.2f}")
    else:
        logger.info(f"Analyze: No opportunity (threshold={min_threshold} bps)")
    
    state["opportunities"] = opportunities
    state["analysis_metadata"] = {
        "ema": ema,
        "deviation_bps": deviation_bps,
        "threshold_bps": min_threshold
    }
    
    return state
