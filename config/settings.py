"""Configuration settings for YieldBot AI."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class SolanaConfig(BaseSettings):
    rpc_url: str = Field(default="https://api.devnet.solana.com", description="Solana RPC URL")
    ws_url: str = Field(default="wss://api.devnet.solana.com", description="Solana WebSocket URL")
    
    class Config:
        extra = "ignore"


class JupiterConfig(BaseSettings):
    api_url: str = Field(default="https://quote-api.jup.ag/v6", description="Jupiter API URL")
    
    class Config:
        extra = "ignore"


class AnalyzerConfig(BaseSettings):
    ema_period: int = Field(default=10, description="EMA period for price calculation")
    min_profit_threshold_bps: int = Field(default=50, description="Minimum profit threshold in basis points")
    max_deviation_bps: int = Field(default=500, description="Maximum deviation before marking as suspicious")
    max_hops: int = Field(default=2, description="Maximum number of hops in route")
    
    class Config:
        extra = "ignore"


class ExecutorConfig(BaseSettings):
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    priority_fee_static: int = Field(default=50000, description="Static priority fee in micro-lamports/CU")
    slippage_bps: int = Field(default=50, description="Slippage tolerance in basis points")
    
    class Config:
        extra = "ignore"


class MonitorConfig(BaseSettings):
    degraded_failure_threshold: int = Field(default=2, description="Consecutive failures for degraded status")
    critical_failure_threshold: int = Field(default=5, description="Consecutive failures for critical status")
    degraded_success_rate_threshold: float = Field(default=0.8, description="Success rate threshold for degraded")
    critical_success_rate_threshold: float = Field(default=0.5, description="Success rate threshold for critical")
    cooldown_minutes: int = Field(default=5, description="Cooldown period in minutes")
    
    class Config:
        extra = "ignore"


class OpenAIConfig(BaseSettings):
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="gpt-4o", description="OpenAI model")
    
    class Config:
        extra = "ignore"


class Settings(BaseSettings):
    solana: SolanaConfig = Field(default_factory=SolanaConfig)
    jupiter: JupiterConfig = Field(default_factory=JupiterConfig)
    analyzer: AnalyzerConfig = Field(default_factory=AnalyzerConfig)
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
