"""Main Telegram Bot service."""

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart

from config import get_settings
from .handlers import BotHandlers

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Service for managing Telegram bot for configuration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.handlers: Optional[BotHandlers] = None
    
    async def initialize(self) -> bool:
        """Initialize the bot."""
        if not self.settings.bot.token:
            logger.warning("Bot token not provided, bot service will not start")
            return False
        
        try:
            self.bot = Bot(
                token=self.settings.bot.token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            self.dp = Dispatcher()
            self.handlers = BotHandlers()
            
            # Register handlers
            self._register_handlers()
            
            logger.info("Telegram bot service initialized")
            return True
            
        except Exception as e:
            logger.exception("Failed to initialize bot service")
            return False
    
    def _register_handlers(self) -> None:
        """Register message and callback handlers."""
        if not self.dp or not self.handlers:
            return
        
        # Admin filter
        admin_filter = F.from_user.id.in_(self.settings.mirror.admin_user_ids)
        
        # Command handlers
        self.dp.message.register(
            self.handlers.handle_start_command, 
            CommandStart(), 
            admin_filter
        )
        self.dp.message.register(
            self.handlers.handle_settings_command, 
            Command("settings"), 
            admin_filter
        )
        self.dp.message.register(
            self.handlers.handle_mirrors_command, 
            Command("mirrors"), 
            admin_filter
        )
        self.dp.message.register(
            self.handlers.handle_chats_command, 
            Command("chats"), 
            admin_filter
        )
        self.dp.message.register(
            self.handlers.handle_users_command, 
            Command("users"), 
            admin_filter
        )
        self.dp.message.register(
            self.handlers.handle_stats_command, 
            Command("stats"), 
            admin_filter
        )
        
        # Callback handlers
        self.dp.callback_query.register(
            self.handlers.handle_callback_query,
            admin_filter
        )
        
        logger.info("Bot handlers registered")
    
    async def start(self) -> None:
        """Start the bot."""
        if not self.bot or not self.dp:
            logger.warning("Bot not initialized, cannot start")
            return
        
        try:
            # Delete webhook and start polling
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Get bot info
            bot_info = await self.bot.get_me()
            logger.info(f"Bot started: @{bot_info.username}")
            
            # Start polling
            await self.dp.start_polling(
                self.bot, 
                allowed_updates=self.dp.resolve_used_update_types()
            )
            
        except Exception as e:
            logger.exception("Error starting bot")
    
    async def stop(self) -> None:
        """Stop the bot."""
        if self.bot:
            await self.bot.session.close()
            logger.info("Bot stopped") 