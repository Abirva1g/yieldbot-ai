"""Main entry point for YieldBot AI."""
import asyncio
import signal
import sys
import logging
from datetime import datetime
from agents.state import BotState, HealthStatus
from agents.planner import planner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    logger.info("\nShutdown requested, finishing current iteration...")
    shutdown_requested = True


async def main():
    """Main loop for YieldBot AI."""
    global shutdown_requested
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("Starting YieldBot AI - Autonomous DeFi Agent")
    logger.info("=" * 60)
    
    # Initialize state
    initial_state: BotState = {
        "session_id": f"session_{datetime.utcnow().timestamp()}",
        "iteration_count": 0,
        "market_data": None,
        "price_history": [],
        "opportunities": [],
        "analysis_metadata": {},
        "selected_plan": None,
        "trade_result": None,
        "execution_history": [],
        "execution_metadata": {},
        "health_status": HealthStatus.HEALTHY,
        "cooldown_until": None,
        "consecutive_failures": 0,
        "last_successful_trade": None,
        "dynamic_config_overrides": {}
    }
    
    state = initial_state
    iteration = 0
    
    try:
        while not shutdown_requested:
            iteration += 1
            logger.info(f"\n{'='*40}")
            logger.info(f"Iteration {iteration} starting...")
            logger.info(f"{'='*40}")
            
            # Run one iteration of the graph
            try:
                # LangGraph использует invoke для запуска
                state = await planner.ainvoke(state)
                
                # Log iteration summary
                health = state.get("health_status", "unknown")
                opportunities = len(state.get("opportunities", []))
                trade_result = state.get("trade_result")
                
                logger.info(f"Iteration {iteration} complete:")
                logger.info(f"  - Health Status: {health}")
                logger.info(f"  - Opportunities Found: {opportunities}")
                
                if trade_result:
                    status = "SUCCESS" if trade_result["success"] else "FAILED"
                    logger.info(f"  - Trade Result: {status}")
                    if trade_result["tx_hash"]:
                        logger.info(f"  - TX Hash: {trade_result['tx_hash']}")
                
                # Handle paused state with delay
                if health == HealthStatus.PAUSED:
                    cooldown_until = state.get("cooldown_until")
                    if cooldown_until:
                        delay_seconds = (cooldown_until - datetime.utcnow()).total_seconds()
                        if delay_seconds > 0:
                            logger.info(f"System paused. Waiting {delay_seconds:.0f}s before resuming...")
                            # Wait in small chunks to allow shutdown
                            wait_time = min(delay_seconds, 5.0)
                            await asyncio.sleep(wait_time)
                            continue
                
                # Small delay between iterations to avoid rate limits
                await asyncio.sleep(2.0)
                
            except Exception as e:
                logger.error(f"Iteration {iteration} failed with error: {e}", exc_info=True)
                # Don't fail completely, continue to next iteration
                await asyncio.sleep(5.0)
        
        logger.info("\n" + "=" * 60)
        logger.info("YieldBot AI shutting down gracefully...")
        logger.info(f"Total iterations completed: {iteration}")
        logger.info(f"Final health status: {state.get('health_status', 'unknown')}")
        logger.info(f"Total trades executed: {len(state.get('execution_history', []))}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown complete.")
