"""Main entry point for Telegram Mirror Bot."""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from config import configure_logging, get_settings
from services import TelegramBotService, TelegramUserService

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""
    
    # Load settings and configure logging
    settings = get_settings()
    configure_logging(settings)
    
    logger.info("Starting Telegram Mirror Bot")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Check for TgCrypto
    try:
        import TgCrypto
        logger.info(f"TgCrypto available - using fast encryption (version {TgCrypto.__version__})")
    except ImportError:
        logger.warning("TgCrypto not installed - using slower encryption. Install with: pip install TgCrypto")
    except Exception as e:
        logger.warning(f"TgCrypto found but not working properly: {e}")
    
    # Create necessary directories
    Path("sessions").mkdir(exist_ok=True)
    Path("rendered_messages").mkdir(exist_ok=True)
    
    # Initialize services
    telegram_service = TelegramUserService()
    bot_service = TelegramBotService()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(shutdown(telegram_service, bot_service))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize bot service
        bot_initialized = await bot_service.initialize()
        if bot_initialized:
            logger.info("Bot service will run alongside user service")
        
        # Initialize telegram service
        try:
            await telegram_service.initialize()
            logger.info("Telegram user service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Telegram user service, continuing with bot only")
            if bot_initialized:
                await bot_service.start()
            else:
                logger.error("No services available, exiting")
                sys.exit(1)
            return
        
        # Start both services concurrently
        if bot_initialized:
            await asyncio.gather(
                telegram_service.start(),
                bot_service.start(),
                return_exceptions=True
            )
        else:
            await telegram_service.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception("Unexpected error occurred")
        sys.exit(1)
    finally:
        await shutdown(telegram_service, bot_service)


async def shutdown(telegram_service: TelegramUserService, bot_service: TelegramBotService) -> None:
    """Perform graceful shutdown."""
    logger.info("Shutting down services...")
    
    try:
        await asyncio.gather(
            telegram_service.stop(),
            bot_service.stop(),
            return_exceptions=True
        )
        logger.info("All services stopped")
    except Exception as e:
        logger.exception("Error during shutdown")
    
    logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception("Fatal error occurred")
        sys.exit(1)