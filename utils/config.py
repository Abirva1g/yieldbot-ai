"""
Legacy config module for backwards compatibility.
Re-exports settings from config.settings module.
Provides flat attribute access for common settings.
"""
from config.settings import settings, Settings

# Backwards compatibility: expose common settings as flat attributes
class ConfigWrapper:
    def __init__(self, settings):
        self._settings = settings
    
    @property
    def solana_rpc_url(self):
        return self._settings.solana.rpc_url
    
    @property
    def solana_ws_url(self):
        return self._settings.solana.ws_url
    
    @property
    def jupiter_api_url(self):
        return self._settings.jupiter.api_url
    
    @property
    def min_profit_threshold_bps(self):
        return self._settings.analyzer.min_profit_threshold_bps
    
    @property
    def ema_period(self):
        return self._settings.analyzer.ema_period
    
    @property
    def max_deviation_bps(self):
        return self._settings.analyzer.max_deviation_bps
    
    @property
    def max_hops(self):
        return self._settings.analyzer.max_hops
    
    @property
    def max_retries(self):
        return self._settings.executor.max_retries
    
    @property
    def priority_fee_static(self):
        return self._settings.executor.priority_fee_static
    
    @property
    def slippage_bps(self):
        return self._settings.executor.slippage_bps
    
    @property
    def openai_api_key(self):
        return self._settings.openai.api_key
    
    @property
    def telegram_bot_token(self):
        return self._settings.telegram.bot_token
    
    @property
    def telegram_chat_id(self):
        return self._settings.telegram.chat_id
    
    @property
    def wallet_private_key(self):
        import os
        return os.getenv("WALLET_PRIVATE_KEY", "")

# Create wrapper instance for backwards compatibility
_config_wrapper = ConfigWrapper(settings)

# Export wrapper attributes as module-level attributes
def __getattr__(name):
    if hasattr(_config_wrapper, name):
        return getattr(_config_wrapper, name)
    raise AttributeError(f"module 'utils.config' has no attribute '{name}'")

__all__ = ["settings", "Settings"] + [
    "solana_rpc_url", "solana_ws_url", "jupiter_api_url",
    "min_profit_threshold_bps", "ema_period", "max_deviation_bps", "max_hops",
    "max_retries", "priority_fee_static", "slippage_bps",
    "openai_api_key", "telegram_bot_token", "telegram_chat_id", "wallet_private_key"
]
