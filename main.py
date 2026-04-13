"""Main entry point for YieldBot AI."""
import asyncio
import signal
import sys
import logging
from datetime import datetime
from agents.state import BotState, HealthStatus
from agents.planner import planner
from utils.telegram_logger import telegram_logger

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
    
    # Send startup notification to Telegram
    try:
        await telegram_logger.send_startup_notification()
    except Exception as e:
        logger.warning(f"Failed to send startup Telegram notification: {e}")
    
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
    trades_count = 0
    
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
                    
                    # Отправляем уведомление о сделке в Telegram
                    try:
                        if trade_result.get("success"):
                            await telegram_logger.send_trade_summary(
                                success=True,
                                tx_hash=trade_result.get("tx_hash"),
                                profit_bps=trade_result.get("profit_bps", 0),
                                details=f"Trade executed in iteration {iteration}"
                            )
                            trades_count += 1
                        elif not trade_result.get("success") and trade_result.get("error"):
                            await telegram_logger.send_alert(
                                title="Trade Failed",
                                message=f"Error: {trade_result['error']}"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to send trade Telegram notification: {e}")
                
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
                # Try to send error notification
                try:
                    await telegram_logger.send_alert(
                        title="Iteration Error",
                        message=str(e)[:200]
                    )
                except:
                    pass
                # Don't fail completely, continue to next iteration
                await asyncio.sleep(5.0)
        
        logger.info("\n" + "=" * 60)
        logger.info("YieldBot AI shutting down gracefully...")
        logger.info(f"Total iterations completed: {iteration}")
        logger.info(f"Final health status: {state.get('health_status', 'unknown')}")
        logger.info(f"Total trades executed: {trades_count}")
        logger.info("=" * 60)
        
        # Send shutdown notification
        try:
            await telegram_logger.send_shutdown_notification(reason="User requested shutdown")
        except Exception as e:
            logger.warning(f"Failed to send shutdown Telegram notification: {e}")
        
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        try:
            await telegram_logger.send_alert(
                title="Fatal Error",
                message=str(e)[:200]
            )
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown complete.")
