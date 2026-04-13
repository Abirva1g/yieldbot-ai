import httpx
from typing import Optional, Dict, Any
from utils.logging_config import logger
from config.settings import settings

JUPITER_QUOTE_API = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"

# Devnet Mints
MINT_SOL = "So11111111111111111111111111111111111111112"
MINT_USDC = "4zMMC9srt5Ri5X14GKXgoVGjQwNpATsUaeYr6DLyquLf"

class JupiterService:
    def __init__(self, use_mock: bool = False):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.use_mock = use_mock
        # Use nested settings structure
        self.is_devnet = "devnet" in settings.solana.rpc_url.lower()
        
    async def get_quote(self, amount: int, slippage_bps: int = 50) -> Optional[Dict[str, Any]]:
        """Fetch quote from Jupiter Aggregator v6 API"""
        if self.use_mock:
            logger.info("Using mock quote data")
            return {
                "inputMint": MINT_SOL,
                "outputMint": MINT_USDC,
                "inAmount": str(amount),
                "outAmount": str(int(amount * 143.5)),
                "priceImpactPct": "0.01",
                "routePlan": [{"swapInfo": {"label": "Raydium"}}]
            }
            
        try:
            response = await self.client.get(
                JUPITER_QUOTE_API,
                params={
                    "inputMint": MINT_SOL,
                    "outputMint": MINT_USDC,
                    "amount": amount,
                    "slippageBps": slippage_bps
                }
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Quote fetched: {data.get('outAmount', 'N/A')} USDC")
                return data
            else:
                logger.error(f"Jupiter API error: {response.status_code} - {response.text}")
                return None
        except httpx.TimeoutException:
            logger.error("Jupiter API timeout")
            return None
        except Exception as e:
            logger.error(f"Error fetching quote: {e}")
            return None
    
    async def get_swap_transaction(self, quote_response: Dict[str, Any], user_public_key: str) -> Optional[str]:
        """Get serialized swap transaction from Jupiter"""
        if self.use_mock:
            logger.info("Using mock swap transaction")
            return "mock_serialized_transaction_bytes"
            
        try:
            response = await self.client.post(
                JUPITER_SWAP_API,
                json={
                    "quoteResponse": quote_response,
                    "userPublicKey": user_public_key,
                    "wrapAndUnwrapSol": True,
                    "dynamicComputeUnitLimit": True,
                    "prioritizationFeeLamports": settings.priority_fee_microlamports
                }
            )
            if response.status_code == 200:
                data = response.json()
                swap_tx = data.get("swapTransaction")
                if swap_tx:
                    logger.info("Swap transaction built successfully")
                    return swap_tx
                return None
            else:
                logger.error(f"Jupiter Swap API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error building swap transaction: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()

jupiter_service = JupiterService()
