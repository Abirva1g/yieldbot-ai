"""Executor Agent for trade execution."""
import logging
from datetime import datetime
from typing import Optional
import asyncio
from agents.state import BotState, Opportunity, TradeResult
from config.settings import settings

logger = logging.getLogger(__name__)

# Error classification
RETRYABLE_ERRORS = ["Blockhash not found", "Timeout", "network", "connection", "rate limit"]
PERMANENT_ERRORS = ["Insufficient funds", "Slippage exceeded", "Account not found", "invalid"]


async def execute_trade(state: BotState) -> BotState:
    """Execute trade based on selected opportunity."""
    logger.info("Execute: Starting trade execution")
    
    opportunities = state.get("opportunities", [])
    if not opportunities:
        logger.info("Execute: No opportunities to execute")
        state["trade_result"] = None
        state["execution_metadata"] = {"reason": "no_opportunities"}
        return state
    
    # Select best opportunity (lowest risk score)
    best_opportunity = min(opportunities, key=lambda x: x["risk_score"])
    logger.info(f"Execute: Selected opportunity {best_opportunity['id']} with risk={best_opportunity['risk_score']:.2f}")
    
    # Execute with retry logic
    max_retries = settings.executor.max_retries
    base_delay = 1.0
    trade_result: Optional[TradeResult] = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Execute: Attempt {attempt + 1}/{max_retries}")
            
            # Simulate trade execution (MVP - no real transaction)
            # In production, this would call Jupiter /swap endpoint and sign transaction
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Simulate success for MVP
            # In production, this would be actual transaction result
            trade_result = TradeResult(
                success=True,
                tx_hash=f"simulated_tx_{datetime.utcnow().timestamp()}",
                actual_return_bps=best_opportunity["expected_return_bps"] * 0.95,  # Simulate some slippage
                error_message=None,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Execute: Trade successful! TX: {trade_result['tx_hash']}")
            break
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Execute: Attempt {attempt + 1} failed: {error_msg}")
            
            # Check if error is retryable
            is_retryable = any(err.lower() in error_msg.lower() for err in RETRYABLE_ERRORS)
            is_permanent = any(err.lower() in error_msg.lower() for err in PERMANENT_ERRORS)
            
            if is_permanent or (not is_retryable and attempt >= max_retries - 1):
                trade_result = TradeResult(
                    success=False,
                    tx_hash=None,
                    actual_return_bps=None,
                    error_message=error_msg,
                    timestamp=datetime.utcnow()
                )
                logger.error(f"Execute: Trade failed permanently: {error_msg}")
                break
            
            if attempt < max_retries - 1:
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                logger.info(f"Execute: Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
    
    # Update state
    state["trade_result"] = trade_result
    state["execution_metadata"] = {
        "attempts": attempt + 1,
        "opportunity_id": best_opportunity["id"]
    }
    
    # Update execution history
    if trade_result:
        history = state.get("execution_history", [])
        history.append(trade_result)
        state["execution_history"] = history
        
        # Update consecutive failures and last successful trade
        if trade_result["success"]:
            state["consecutive_failures"] = 0
            state["last_successful_trade"] = datetime.utcnow()
        else:
            state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    
    return state
