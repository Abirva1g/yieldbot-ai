"""Monitor Agent for health checking and self-healing."""
import logging
from datetime import datetime, timedelta
from typing import List
from agents.state import BotState, TradeResult, HealthStatus
from config.settings import settings

logger = logging.getLogger(__name__)


def calculate_success_rate(history: List[TradeResult], window: int) -> float:
    """Calculate success rate over last N trades."""
    if not history:
        return 1.0
    
    recent = history[-window:]
    if not recent:
        return 1.0
    
    successes = sum(1 for t in recent if t["success"])
    return successes / len(recent)


async def check_and_heal(state: BotState) -> BotState:
    """Check health status and apply self-healing actions."""
    logger.info("Monitor: Checking health status")
    
    consecutive_failures = state.get("consecutive_failures", 0)
    execution_history = state.get("execution_history", [])
    current_status = state.get("health_status", HealthStatus.HEALTHY)
    cooldown_until = state.get("cooldown_until")
    
    # Check if cooldown has expired
    if current_status == HealthStatus.PAUSED and cooldown_until:
        if datetime.utcnow() > cooldown_until:
            logger.info("Monitor: Cooldown expired, resuming operations")
            current_status = HealthStatus.DEGRADED
            state["cooldown_until"] = None
        else:
            remaining = (cooldown_until - datetime.utcnow()).total_seconds()
            logger.info(f"Monitor: Still in cooldown for {remaining:.0f}s")
            state["health_status"] = HealthStatus.PAUSED
            return state
    
    # Determine health status
    new_status = HealthStatus.HEALTHY
    
    # Check critical conditions
    if consecutive_failures >= settings.monitor.critical_failure_threshold:
        new_status = HealthStatus.CRITICAL
        logger.warning(f"Monitor: Critical status - {consecutive_failures} consecutive failures")
    elif calculate_success_rate(execution_history, 20) < settings.monitor.critical_success_rate_threshold:
        new_status = HealthStatus.CRITICAL
        logger.warning("Monitor: Critical status - success rate < 50% in last 20 trades")
    
    # Check degraded conditions (if not already critical)
    elif consecutive_failures >= settings.monitor.degraded_failure_threshold:
        new_status = HealthStatus.DEGRADED
        logger.warning(f"Monitor: Degraded status - {consecutive_failures} consecutive failures")
    elif calculate_success_rate(execution_history, 10) < settings.monitor.degraded_success_rate_threshold:
        new_status = HealthStatus.DEGRADED
        logger.warning("Monitor: Degraded status - success rate < 80% in last 10 trades")
    
    # Apply self-healing actions
    dynamic_overrides = state.get("dynamic_config_overrides", {})
    
    if new_status == HealthStatus.CRITICAL:
        # Pause trading
        cooldown_minutes = settings.monitor.cooldown_minutes
        state["cooldown_until"] = datetime.utcnow() + timedelta(minutes=cooldown_minutes)
        new_status = HealthStatus.PAUSED
        logger.error(f"Monitor: PAUSING trading for {cooldown_minutes} minutes")
        
    elif new_status == HealthStatus.DEGRADED:
        # Increase priority fee by 50% for next trades
        dynamic_overrides["priority_fee_multiplier"] = 1.5
        logger.info("Monitor: Increased priority fee by 50% due to degraded status")
        
        # Check for false positives and adjust threshold
        false_positives = sum(
            1 for t in execution_history[-10:]
            if not t["success"] and t.get("error_message") and "slippage" in t.get("error_message", "").lower()
        )
        
        if false_positives > 5:
            current_threshold = settings.analyzer.min_profit_threshold_bps
            new_threshold = current_threshold + 10
            dynamic_overrides["min_profit_threshold_bps"] = new_threshold
            logger.info(f"Monitor: Increased profit threshold to {new_threshold} bps due to false positives")
    
    else:
        # Reset overrides when healthy
        dynamic_overrides = {}
        logger.info("Monitor: System healthy, reset overrides")
    
    # Update state
    state["health_status"] = new_status
    state["dynamic_config_overrides"] = dynamic_overrides
    
    # Log health summary
    success_rate_10 = calculate_success_rate(execution_history, 10)
    success_rate_20 = calculate_success_rate(execution_history, 20)
    logger.info(
        f"Monitor: Health={new_status}, Failures={consecutive_failures}, "
        f"SuccessRate(10)={success_rate_10:.1%}, SuccessRate(20)={success_rate_20:.1%}"
    )
    
    return state
