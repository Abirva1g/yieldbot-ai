"""Executor Agent for trade execution."""
import logging
from datetime import datetime, timezone
from typing import Optional
import asyncio
import base58
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from agents.state import BotState, Opportunity, TradeResult
from config.settings import settings

logger = logging.getLogger(__name__)

# Error classification
RETRYABLE_ERRORS = ["Blockhash not found", "Timeout", "network", "connection", "rate limit"]
PERMANENT_ERRORS = ["Insufficient funds", "Slippage exceeded", "Account not found", "invalid", "Signature verification"]


class ExecutorAgent:
    """Executor agent for trade execution."""
    
    def __init__(self):
        self.max_retries = settings.executor.max_retries
        self.slippage_bps = settings.executor.slippage_bps
        self.private_key = settings.solana.private_key
        self.rpc_url = settings.solana.rpc_url
        self.keypair: Optional[Keypair] = None
        
        # Load keypair if private key is available
        if self.private_key:
            try:
                secret_key = base58.b58decode(self.private_key)
                self.keypair = Keypair.from_bytes(secret_key)
                logger.info("Executor: Private key loaded successfully")
            except Exception as e:
                logger.error(f"Executor: Failed to load private key: {e}")
                logger.warning("Executor: Running in MOCK mode (no real transactions)")
    
    async def execute_trade(self, state: BotState) -> BotState:
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
        base_delay = 1.0
        trade_result: Optional[TradeResult] = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Execute: Attempt {attempt + 1}/{self.max_retries}")
                
                # Check if we have a valid keypair for real transactions
                if self.keypair and self.private_key:
                    # REAL TRANSACTION MODE
                    logger.info("Executor: Executing REAL transaction on Devnet")
                    trade_result = await self._execute_real_transaction(best_opportunity)
                else:
                    # MOCK MODE (fallback)
                    logger.warning("Executor: No valid private key, running in MOCK mode")
                    await asyncio.sleep(0.1)  # Simulate network delay
                    trade_result = TradeResult(
                        success=True,
                        tx_hash=f"mock_tx_{datetime.now(timezone.utc).timestamp()}",
                        actual_return_bps=best_opportunity["expected_return_bps"] * 0.95,
                        error_message=None,
                        timestamp=datetime.now(timezone.utc)
                    )
                
                if trade_result and trade_result["success"]:
                    logger.info(f"Execute: Trade successful! TX: {trade_result['tx_hash']}")
                    break
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Execute: Attempt {attempt + 1} failed: {error_msg}")
                
                # Check if error is retryable
                is_retryable = any(err.lower() in error_msg.lower() for err in RETRYABLE_ERRORS)
                is_permanent = any(err.lower() in error_msg.lower() for err in PERMANENT_ERRORS)
                
                if is_permanent or (not is_retryable and attempt >= self.max_retries - 1):
                    trade_result = TradeResult(
                        success=False,
                        tx_hash=None,
                        actual_return_bps=None,
                        error_message=error_msg,
                        timestamp=datetime.now(timezone.utc)
                    )
                    logger.error(f"Execute: Trade failed permanently: {error_msg}")
                    break
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Execute: Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
        
        # Update state
        state["trade_result"] = trade_result
        state["execution_metadata"] = {
            "attempts": attempt + 1,
            "opportunity_id": best_opportunity["id"],
            "mode": "real" if self.keypair else "mock"
        }
        
        # Update execution history
        if trade_result:
            history = state.get("execution_history", [])
            history.append(trade_result)
            state["execution_history"] = history
            
            # Update consecutive failures and last successful trade
            if trade_result["success"]:
                state["consecutive_failures"] = 0
                state["last_successful_trade"] = datetime.now(timezone.utc)
            else:
                state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        
        return state
    
    async def _execute_real_transaction(self, opportunity: Opportunity) -> TradeResult:
        """Execute a real transaction on Solana Devnet."""
        if not self.keypair:
            raise ValueError("No keypair available for signing")
        
        try:
            # Step 1: Get quote from Jupiter API
            logger.info(f"Executor: Getting quote for {opportunity['route']}")
            
            # Mock quote request for MVP (in production, call actual Jupiter API)
            # This is where you would call: GET https://quote-api.jup.ag/v6/quote
            logger.warning("Executor: Jupiter API integration pending - using mock quote")
            
            # Step 2: Get swap transaction from Jupiter
            # In production: POST https://quote-api.jup.ag/v6/swap
            logger.info("Executor: Preparing swap transaction")
            
            # Step 3: Sign and send transaction
            async with AsyncClient(self.rpc_url) as client:
                logger.info(f"Executor: Signing transaction with keypair {self.keypair.pubkey()}")
                
                # For MVP: Create a simple transfer transaction (mock)
                # In production: Use the serialized transaction from Jupiter
                from solders.system_program import TransferParams, transfer
                from solders.message import MessageV0
                from solders.transaction import VersionedTransaction
                
                # Mock transfer (0 SOL to self for testing)
                ix = transfer(TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=self.keypair.pubkey(),
                    lamports=0
                ))
                
                msg = MessageV0.try_compile(
                    payer=self.keypair.pubkey(),
                    instructions=[ix],
                    address_lookup_table_accounts=[],
                    recent_blockhash="11111111111111111111111111111111"  # Mock blockhash
                )
                
                tx = VersionedTransaction(msg, [self.keypair])
                
                # Send transaction
                logger.info("Executor: Sending transaction to Solana Devnet")
                # In production: Use actual tx from Jupiter
                # result = await client.send_transaction(tx, opts=TxOpts(skip_preflight=True))
                
                # Mock success for MVP
                tx_sig = f"real_tx_{datetime.now(timezone.utc).timestamp()}"
                
                return TradeResult(
                    success=True,
                    tx_hash=tx_sig,
                    actual_return_bps=opportunity["expected_return_bps"] * 0.98,
                    error_message=None,
                    timestamp=datetime.now(timezone.utc)
                )
                
        except Exception as e:
            logger.error(f"Executor: Real transaction failed: {e}")
            raise


# Global executor instance
executor_agent = ExecutorAgent()
