import os
import sys

# Структура файлов и их содержимое
files = {
    "requirements.txt": """langgraph==0.2.6
langchain-openai==0.1.7
httpx==0.27.0
solders==0.21.0
solana==0.32.0
pydantic==2.7.4
pydantic-settings==2.3.4
python-dotenv==1.0.1
pytest==8.2.2
pytest-asyncio==0.23.7
""",

    ".env.example": """# Solana Network (Devnet)
SOLANA_RPC_URL=https://api.devnet.solana.com

# Wallet Security (DEVNET KEY ONLY)
WALLET_PRIVATE_KEY=your_base58_private_key_here

# OpenAI (Optional for MVP logic)
OPENAI_API_KEY=sk-your-key-here

# Telegram Alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Strategy Config
MIN_PROFIT_THRESHOLD_BPS=50
EMA_PERIOD=10
PRIORITY_FEE_MICROLAMPORTS=50000
""",

    "Dockerfile": """FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import agents.planner; print('OK')" || exit 1

CMD ["python", "main.py"]
""",

    "docker-compose.yml": """version: '3.8'

services:
  yieldbot:
    build: .
    container_name: yieldbot-ai
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
""",

    "config/__init__.py": "",
    
    "config/settings.py": """from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    solana_rpc_url: str = "https://api.devnet.solana.com"
    wallet_private_key: str = ""
    openai_api_key: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Strategy
    min_profit_threshold_bps: int = 50
    ema_period: int = 10
    priority_fee_microlamports: int = 50000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
""",

    "utils/__init__.py": "",

    "utils/logging_config.py": """import logging
import sys
import os

def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "yieldbot.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("YieldBot")

logger = setup_logger()
""",

    "services/__init__.py": "",

    "services/jupiter_service.py": """import httpx
from typing import Optional, Dict
from utils.logging_config import logger
from config.settings import settings

JUPITER_QUOTE_API = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"

# Devnet Mints
MINT_SOL = "So11111111111111111111111111111111111111112"
MINT_USDC = "4zMMC9srt5Ri5X14GKXgoVGjQwNpATsUaeYr6DLyquLf"

class JupiterService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_quote(self, amount: int, slippage_bps: int = 50) -> Optional[Dict]:
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
                logger.info(f"Jupiter Quote: {data.get('outAmount', 'N/A')} USDC for {amount} SOL")
                return data
            logger.warning(f"Jupiter API error: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching quote: {e}")
            return None

    async def get_swap_transaction(self, quote_response: Dict, user_public_key: str) -> Optional[str]:
        try:
            response = await self.client.post(
                JUPITER_SWAP_API,
                json={
                    "quoteResponse": quote_response,
                    "userPublicKey": user_public_key,
                    "wrapAndUnwrapSol": True
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("swapTransaction")
            return None
        except Exception as e:
            logger.error(f"Error fetching swap tx: {e}")
            return None

jupiter_service = JupiterService()
""",

    "agents/__init__.py": "",

    "agents/analyzer.py": """from typing import List, Dict
from utils.logging_config import logger
from config.settings import settings

class AnalyzerAgent:
    def analyze_market_data(self, price_history: List[float]) -> bool:
        if len(price_history) < 2:
            return False
        
        current_price = price_history[-1]
        avg_price = sum(price_history) / len(price_history)
        
        if avg_price == 0:
            return False
            
        deviation = abs(current_price - avg_price) / avg_price * 10000 # in bps
        
        if deviation > settings.min_profit_threshold_bps:
            logger.info(f"Opportunity detected! Deviation: {deviation:.2f} bps (Threshold: {settings.min_profit_threshold_bps})")
            return True
        return False

analyzer_agent = AnalyzerAgent()
""",

    "agents/executor.py": """from utils.logging_config import logger

class ExecutorAgent:
    async def execute_trade(self, opportunity: dict):
        logger.info("Executing trade (Simulation Mode for MVP)...")
        # Here we would integrate solders and real signing
        return {"status": "success", "tx_hash": "simulated_tx_hash"}

executor_agent = ExecutorAgent()
""",

    "agents/monitor.py": """from utils.logging_config import logger

class MonitorAgent:
    def check_health(self) -> str:
        # Simple health check logic
        return "HEALTHY"

monitor_agent = MonitorAgent()
""",

    "agents/planner.py": """from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from utils.logging_config import logger
from agents.analyzer import analyzer_agent
from agents.executor import executor_agent
from agents.monitor import monitor_agent

class BotState(TypedDict):
    price_history: List[float]
    iteration_count: int
    has_opportunity: bool

def perceive_node(state: BotState):
    # Simulate price fetch (Mock data for stability until API key is set)
    import random
    base_price = 143.50
    new_price = base_price + random.uniform(-2, 2)
    state["price_history"].append(new_price)
    if len(state["price_history"]) > 20:
        state["price_history"].pop(0)
    logger.info(f"Perceive: New price ${new_price:.2f}")
    return state

def analyze_node(state: BotState):
    has_opportunity = analyzer_agent.analyze_market_data(state["price_history"])
    state["has_opportunity"] = has_opportunity
    return state

def execute_node(state: BotState):
    if state.get("has_opportunity"):
        logger.info("Plan: Opportunity found, executing...")
        # executor_agent.execute_trade(...)
    else:
        logger.info("Plan: No opportunity, skipping.")
    return state

def monitor_node(state: BotState):
    status = monitor_agent.check_health()
    logger.info(f"Monitor: Health Status [{status}]")
    state["iteration_count"] += 1
    return state

# Build Graph
workflow = StateGraph(BotState)
workflow.add_node("perceive", perceive_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("execute", execute_node)
workflow.add_node("monitor", monitor_node)

workflow.set_entry_point("perceive")
workflow.add_edge("perceive", "analyze")
workflow.add_edge("analyze", "execute")
workflow.add_edge("execute", "monitor")
workflow.add_edge("monitor", "perceive") # Loop back

app = workflow.compile()
""",

    "main.py": """import asyncio
from agents.planner import app
from utils.logging_config import logger
from config.settings import settings

async def main():
    logger.info("🚀 Starting YieldBot AI...")
    logger.info(f"Config: Devnet={settings.solana_rpc_url}, Threshold={settings.min_profit_threshold_bps}bps")
    
    initial_state = {
        "price_history": [],
        "iteration_count": 0,
        "has_opportunity": False
    }
    
    try:
        while True:
            # Run one iteration of the graph
            result = await app.ainvoke(initial_state)
            initial_state = result # Pass state to next iteration
            
            # Wait 10 seconds between iterations
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("🛑 Graceful shutdown requested...")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
"""
}

def create_project():
    print("🚀 Starting YieldBot AI Project Generation...")
    
    for filepath, content in files.items():
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")
        
        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 Created file: {filepath}")
    
    print("\n✅ Project structure generated successfully!")
    print("\nNext steps:")
    print("1. Review the created files.")
    print("2. Run: git add .")
    print("3. Run: git commit -m 'feat: Complete YieldBot AI MVP structure'")
    print("4. Run: git push origin main")

if __name__ == "__main__":
    create_project()
