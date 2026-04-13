"""
Legacy config module for backwards compatibility.
Re-exports settings from config.settings module.
"""
from config.settings import settings, Settings

__all__ = ["settings", "Settings"]
