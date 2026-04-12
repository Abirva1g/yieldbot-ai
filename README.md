# YieldBot AI - Autonomous DeFi Agent

An autonomous, serverless DeFi yield aggregator that operates without human intervention after initial setup.

## Features

- **Autonomous Operation**: Self-healing, self-monitoring, executes trades autonomously
- **Multi-Agent Architecture**: LangGraph-based state machine with Perceive → Analyze → Plan → Execute → Monitor loop
- **Solana Integration**: Jupiter Aggregator v6 for optimal trade routing
- **Risk Management**: Dynamic risk scoring, slippage protection, consecutive failure detection
- **Self-Healing**: Automatic cooldowns, threshold adjustments, and congestion-aware fee boosting

## Project Structure

```
yieldbot_ai/
├── agents/
│   ├── state.py           # BotState TypedDict definitions
│   ├── planner.py         # Main LangGraph workflow orchestration
│   ├── analyzer.py        # Opportunity detection with EMA
│   ├── executor.py        # Trade execution with retry logic
│   └── monitor.py         # Health checking and self-healing
├── config/
│   ├── __init__.py
│   └── settings.py        # Pydantic configuration classes
├── services/              # External API integrations (Phase 2)
├── utils/                 # Shared utilities (Phase 2)
├── tests/                 # Test suites
├── main.py                # Entry point with infinite loop
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
└── .env.example          # Environment template
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (Devnet configured by default)
```

### 3. Run the Bot

```bash
python main.py
```

## Configuration

Key parameters in `.env`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ANALYZER_EMA_PERIOD` | 10 | EMA period for price baseline |
| `ANALYZER_MIN_PROFIT_THRESHOLD_BPS` | 50 | Minimum profit threshold (0.5%) |
| `EXECUTOR_MAX_RETRIES` | 3 | Max retry attempts per trade |
| `MONITOR_COOLDOWN_MINUTES` | 5 | Cooldown on critical failures |

## Workflow

1. **Perceive**: Fetches SOL/USDC price data from Jupiter API
2. **Analyze**: Calculates EMA, detects price deviations > threshold
3. **Plan**: Selects best opportunity (lowest risk score)
4. **Execute**: Signs and submits transaction with retry logic
5. **Monitor**: Updates health status, applies self-healing actions

## Health Status

- **Healthy**: Normal operation, success rate > 80%
- **Degraded**: 2+ consecutive failures OR success rate < 80%
- **Critical**: 5+ consecutive failures OR success rate < 50%
- **Paused**: Trading halted for 5-minute cooldown

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_analyzer.py -v
```

## Safety Features

- **Devnet First**: Default configuration uses Solana Devnet
- **No Real Funds**: MVP uses simulated transactions
- **Private Key Security**: Keys never logged or exposed
- **Circuit Breakers**: Automatic pause on systemic failures

## Roadmap

- **Phase 1 (MVP)**: ✅ Complete - Core agent loop with simulated execution
- **Phase 2**: Chainlink Functions/CCIP integration, real transaction signing
- **Phase 3**: Confidential Compute, AWS Lambda deployment

## License

MIT
