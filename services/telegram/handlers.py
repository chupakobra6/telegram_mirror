"""Message handlers for Telegram user client."""

import logging
from typing import Optional

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message as PyrogramMessage

from config import get_settings
from database import get_db_manager
from services.mirror import MirrorService
from .commands import AdminCommandHandler

logger = logging.getLogger(__name__)


class TelegramMessageHandler:
    """Handler for Telegram messages and events."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = get_db_manager()
        self.command_handler = AdminCommandHandler()
    
    def setup_handlers(self, client: Client) -> None:
        """Set up message handlers for the client."""
        
        # Create filters for source chats and allowed users
        source_chat_filter = filters.chat(self.settings.mirror.source_chat_ids)
        allowed_user_filter = filters.user(self.settings.mirror.allowed_user_ids)
        
        # Handler for admin commands (highest priority)
        # Allow commands from configured admins OR from the current user account anywhere (filters.me)
        admin_filter = filters.user(self.settings.mirror.admin_user_ids) | filters.me
        command_filter = filters.command(["help", "status", "mirrors", "add_mirror", "remove_mirror", "chats", "copy_message"]) 
        
        client.add_handler(
            MessageHandler(
                self.handle_admin_command,
                admin_filter & command_filter
            )
        )
        
        # Handler for regular messages from source chats
        client.add_handler(
            MessageHandler(
                self.handle_source_message,
                source_chat_filter & allowed_user_filter
            )
        )
        
        # Handler for logging messages in mirror chats (lowest priority)
        mirror_chat_filter = (
            filters.chat(self.settings.mirror.source_chat_ids) |
            filters.chat(self.settings.mirror.target_chat_ids)
        )
        
        client.add_handler(
            MessageHandler(
                self.log_mirror_chat_message,
                mirror_chat_filter
            )
        )
        
        logger.info("Message handlers configured")
    
    async def log_mirror_chat_message(
        self,
        client: Client,
        message: PyrogramMessage
    ) -> None:
        """Log messages in mirror chats for monitoring."""
        try:
            chat_title = (message.chat.title if message.chat and message.chat.title else None) or f"Chat {message.chat.id}"
            
            # Get current user info
            me = await client.get_me()
            my_id = me.id
            
            if message.from_user:
                user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
                username = message.from_user.username
                user_info = f"{user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
                
                # Check if this is an outgoing message (from current user)
                if message.from_user.id == my_id:
                    direction = "📤 Отправлено"
                    preposition = "в чат"
                else:
                    direction = "📥 Получено"
                    preposition = "из чата"
            else:
                user_info = "System/Channel"
                direction = "📥 Получено"
                preposition = "из чата"
            
            message_type = "команда" if message.text and message.text.startswith('/') else "сообщение"
            
            logger.info(
                f"{direction} {message_type} {preposition} '{chat_title}' (ID: {message.chat.id}) "
                f"{'от' if direction == '📥 Получено' else 'для'} {user_info}"
            )
            
        except Exception as e:
            logger.exception("Error logging mirror chat message")
    
    async def handle_source_message(
        self, 
        client: Client, 
        message: PyrogramMessage
    ) -> None:
        """Handle messages from source chats."""
        try:
            # Log incoming message
            chat_title = (message.chat.title if message.chat and message.chat.title else None) or f"Chat {message.chat.id}"
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            
            logger.info(
                f"📥 Получено сообщение из чата '{chat_title}' (ID: {message.chat.id}) "
                f"от пользователя {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            async with self.db_manager.get_session() as session:
                mirror_service = MirrorService(session)
                
                # Process the incoming message
                db_message = await mirror_service.process_incoming_message(message)
                
                if db_message and db_message.is_mirrored:
                    # Get mirrors for this source chat
                    mirrors = await mirror_service.get_mirrors_for_source_chat(message.chat.id)
                    
                    # Send mirrored messages
                    for mirror in mirrors:
                        await self.send_mirrored_message(
                            client, db_message, mirror
                        )
                
        except Exception as e:
            logger.exception(f"Error handling source message {message.id}")
    
    async def send_mirrored_message(
        self,
        client: Client,
        db_message,
        mirror,
    ) -> None:
        """Send a mirrored message to the target chat."""
        try:
            target_chat_id = mirror.target_chat_id
            target_topic_id = mirror.target_topic_id
            
            # Get target chat title for logging
            try:
                target_chat = await client.get_chat(target_chat_id)
                target_chat_title = (target_chat.title if target_chat and target_chat.title else None) or f"Chat {target_chat_id}"
            except:
                target_chat_title = f"Chat {target_chat_id}"
            
            # If message was rendered as image, send the image
            if db_message.rendered_image_path and mirror.render_as_image:
                await client.send_photo(
                    chat_id=target_chat_id,
                    photo=db_message.rendered_image_path,
                    reply_to_message_id=target_topic_id,
                )
                logger.info(f"📤 Отправлено изображение в чат '{target_chat_title}' (ID: {target_chat_id})")
            
            # Otherwise, copy the original message
            else:
                await client.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=db_message.chat_id,
                    message_id=db_message.telegram_id,
                    reply_to_message_id=target_topic_id,
                )
                logger.info(f"📤 Скопировано сообщение в чат '{target_chat_title}' (ID: {target_chat_id})")
                
        except Exception as e:
            logger.exception(f"Error sending mirrored message to {mirror.target_chat_id}")
    
    async def handle_admin_command(
        self, 
        client: Client, 
        message: PyrogramMessage
    ) -> None:
        """Handle admin commands."""
        try:
            logger.info(f"Admin command received: text='{message.text}' chat_id={message.chat.id} from_user_id={(message.from_user.id if message.from_user else None)}")
            command = message.command[0].lower() if message.command else ""
            
            match command:
                case "help":
                    await self.command_handler.handle_help_command(client, message)
                case "status":
                    await self.command_handler.handle_status_command(client, message)
                case "mirrors":
                    await self.command_handler.handle_mirrors_command(client, message)
                case "add_mirror":
                    await self.command_handler.handle_add_mirror_command(client, message)
                case "remove_mirror":
                    await self.command_handler.handle_remove_mirror_command(client, message)
                case "chats":
                    await self.command_handler.handle_chats_command(client, message)
                case "copy_message":
                    await self.command_handler.handle_copy_message_command(client, message)
                case _:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="❌ Unknown command. Use /help for available commands.",
                        reply_to_message_id=message.id,
                    )
                    
        except Exception as e:
            logger.exception(f"Error handling admin command: {command}")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Error processing command.",
                reply_to_message_id=message.id,
            ) 