"""State definitions for YieldBot AI LangGraph workflow."""
from typing import TypedDict, List, Optional, Literal, Annotated
from datetime import datetime
import operator


class MarketData(TypedDict):
    """Perceived market state from Jupiter API."""
    timestamp: datetime
    chain_id: int
    token_pair: str
    price: float
    volume_24h: float
    dex_liquidity: dict


class Opportunity(TypedDict):
    """Identified yield opportunity."""
    id: str
    type: Literal["arbitrage", "yield_farming", "mev_recapture"]
    chain_from: int
    chain_to: int
    expected_return_bps: float
    risk_score: float
    required_capital_usd: float
    expiry_block: int


class TradePlan(TypedDict):
    """Executable trade plan."""
    opportunity_id: str
    actions: List[dict]
    slippage_tolerance_bps: int
    gas_budget_usd: float
    confidence_score: float


class TradeResult(TypedDict):
    """Result of trade execution."""
    success: bool
    tx_hash: Optional[str]
    actual_return_bps: Optional[float]
    error_message: Optional[str]
    timestamp: datetime


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    PAUSED = "paused"


def reduce_opportunities(existing: List[Opportunity], new: List[Opportunity]) -> List[Opportunity]:
    """Reducer for accumulating opportunities."""
    if existing is None:
        return new or []
    return existing + (new or [])


def reduce_execution_history(existing: List[TradeResult], new: List[TradeResult]) -> List[TradeResult]:
    """Reducer for accumulating execution history."""
    if existing is None:
        return new or []
    return existing + (new or [])


def reduce_price_history(existing: List[MarketData], new: List[MarketData]) -> List[MarketData]:
    """Reducer for price history, keeping last N items."""
    if existing is None:
        return new or []
    combined = existing + (new or [])
    return combined[-20:]  # Keep last 20 samples


class BotState(TypedDict):
    """Complete state for YieldBot AI orchestration."""
    # Context
    session_id: str
    iteration_count: int
    
    # Perceive
    market_data: Optional[MarketData]
    price_history: Annotated[List[MarketData], reduce_price_history]
    
    # Analyze
    opportunities: Annotated[List[Opportunity], reduce_opportunities]
    analysis_metadata: dict
    
    # Plan
    selected_plan: Optional[TradePlan]
    
    # Execute
    trade_result: Optional[TradeResult]
    execution_history: Annotated[List[TradeResult], reduce_execution_history]
    execution_metadata: dict
    
    # Monitor
    health_status: str
    cooldown_until: Optional[datetime]
    consecutive_failures: int
    last_successful_trade: Optional[datetime]
    
    # Dynamic config
    dynamic_config_overrides: dict
