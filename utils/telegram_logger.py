"""
Telegram Logger for YieldBot AI
Sends alerts and trade summaries to Telegram
"""

import httpx
import logging
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class TelegramLogger:
    """Async Telegram bot for sending alerts and notifications"""
    
    def __init__(self):
        self.token = settings.telegram.bot_token
        self.chat_id = settings.telegram.chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = bool(self.token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram logging disabled: missing BOT_TOKEN or CHAT_ID")
    
    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to Telegram chat"""
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        logger.error(f"Telegram API error: {result}")
                        return False
                else:
                    logger.error(f"Telegram HTTP error: {response.status_code} - {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error("Telegram request timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_alert(self, title: str, message: str) -> bool:
        """Send a critical alert"""
        full_message = f"🚨 *ALERT: {title}*\n\n{message}"
        return await self.send_message(full_message)
    
    async def send_trade_summary(self, 
                                  success: bool, 
                                  tx_hash: Optional[str], 
                                  profit_bps: float,
                                  details: str) -> bool:
        """Send trade execution summary"""
        emoji = "✅" if success else "❌"
        status = "SUCCESS" if success else "FAILED"
        
        message = f"{emoji} *Trade {status}*\n\n"
        message += f"Profit/Loss: `{profit_bps:.2f} bps`\n"
        
        if tx_hash:
            # Truncate hash for readability
            short_hash = f"{tx_hash[:8]}...{tx_hash[-8:]}"
            message += f"TX: [`{short_hash}`](https://solscan.io/tx/{tx_hash})\n"
        
        if details:
            message += f"\n{details}"
        
        return await self.send_message(message)
    
    async def send_status_update(self, health_status: str, consecutive_failures: int) -> bool:
        """Send health status update"""
        if health_status == "CRITICAL":
            return await self.send_alert(
                "CRITICAL HEALTH STATUS",
                f"Bot health is CRITICAL!\nConsecutive failures: `{consecutive_failures}`\nTrading paused."
            )
        elif health_status == "DEGRADED":
            return await self.send_message(
                f"⚠️ *Health Status: DEGRADED*\n\nConsecutive failures: `{consecutive_failures}`\nMonitoring closely."
            )
        return True
    
    async def send_startup_notification(self) -> bool:
        """Send notification on bot startup"""
        message = (
            "🤖 *YieldBot AI Started*\n\n"
            f"Network: `{settings.solana.network}`\n"
            f"Mode: {'Live' if not settings.solana.rpc_url.endswith('devnet') else 'Devnet'}\n\n"
            "Autonomous trading loop initiated."
        )
        return await self.send_message(message)
    
    async def send_shutdown_notification(self, reason: str = "User request") -> bool:
        """Send notification on bot shutdown"""
        message = f"🛑 *YieldBot AI Stopped*\n\nReason: {reason}\n\nGoodbye!"
        return await self.send_message(message)
    
    async def send_pause_notification(self, paused: bool) -> bool:
        """Send notification when bot is paused/resumed"""
        if paused:
            return await self.send_message("⏸️ *Trading PAUSED*\n\nBot will skip execution until resumed.")
        else:
            return await self.send_message("▶️ *Trading RESUMED*\n\nBot is active again.")


# Global instance
telegram_logger = TelegramLogger()
