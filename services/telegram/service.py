"""Telegram service for managing pyrogram client and message handling."""

import logging
from typing import Optional

from pyrogram import Client, idle

from config import get_settings
from database import get_db_manager
from .handlers import TelegramMessageHandler

logger = logging.getLogger(__name__)


class TelegramUserService:
    """Service for managing Telegram user client operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = get_db_manager()
        self.client: Optional[Client] = None
        self.message_handler: Optional[TelegramMessageHandler] = None
    
    async def initialize(self) -> None:
        """Initialize the Telegram client and database."""
        try:
            # Initialize database
            await self.db_manager.create_tables()
            
            # Initialize Telegram client
            self.client = Client(
                name=self.settings.telegram.session_name,
                api_id=self.settings.telegram.api_id,
                api_hash=self.settings.telegram.api_hash,
                workdir="sessions",  # Store session files in sessions directory
            )
            
            # Initialize message handler
            self.message_handler = TelegramMessageHandler()
            
            # Set up message handlers
            self.message_handler.setup_handlers(self.client)
            
            logger.info("Telegram user service initialized successfully")
            
        except Exception as e:
            logger.exception("Failed to initialize Telegram user service")
            raise
    
    async def start(self) -> None:
        """Start the Telegram client and begin processing messages."""
        if not self.client:
            await self.initialize()
        
        try:
            await self.client.start()
            logger.info("Telegram user client started")
            
            # Get basic client info
            me = await self.client.get_me()
            logger.info(f"Logged in as: {me.first_name} (@{me.username})")
            
            # Start idle loop
            await idle()
            
        except Exception as e:
            logger.exception("Error starting Telegram user client")
            raise
    
    async def stop(self) -> None:
        """Stop the Telegram client and close database connections."""
        try:
            if self.client and self.client.is_connected:
                await self.client.stop()
                logger.info("Telegram user client stopped")
            elif self.client:
                logger.info("Telegram user client was already stopped")
            
            await self.db_manager.close()
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.exception("Error stopping Telegram user service")
    
    def get_client(self) -> Optional[Client]:
        """Get the pyrogram client instance."""
        return self.client
    
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self.client is not None and self.client.is_connected 