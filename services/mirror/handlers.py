"""Message mirroring handlers."""

import logging
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database.models import Chat, Message, Mirror, User
from database.repositories import (
    ChatRepository,
    MessageRepository, 
    MirrorRepository,
    UserRepository,
)
from services.renderer import MessageRenderer
from .processors import MessageProcessor

logger = logging.getLogger(__name__)


class MirrorHandler:
    """Handler for message mirroring operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        
        # Initialize repositories
        self.user_repo = UserRepository(session)
        self.chat_repo = ChatRepository(session)
        self.message_repo = MessageRepository(session)
        self.mirror_repo = MirrorRepository(session)
        
        # Initialize processor and renderer
        self.processor = MessageProcessor()
        self.renderer = MessageRenderer()
    
    async def ensure_user_exists(self, user_info: dict) -> Optional[User]:
        """Ensure user exists in database."""
        if not user_info:
            return None
        
        user_id = user_info["user_id"]
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            # Check if user should be allowed
            is_admin = user_id in self.settings.mirror.admin_user_ids
            is_allowed = (
                is_admin or 
                user_id in self.settings.mirror.allowed_user_ids
            )
            
            user = await self.user_repo.create(
                user_id=user_id,
                username=user_info["username"],
                first_name=user_info["first_name"],
                last_name=user_info["last_name"],
                is_admin=is_admin,
                is_allowed=is_allowed,
            )
            logger.info(f"Created new user: {user}")
        
        return user
    
    async def ensure_chat_exists(self, chat_info: dict) -> Chat:
        """Ensure chat exists in database."""
        chat_id = chat_info["chat_id"]
        chat = await self.chat_repo.get_by_id(chat_id)
        
        if not chat:
            # Check if this is a source or target chat
            is_source = chat_id in self.settings.mirror.source_chat_ids
            is_target = chat_id in self.settings.mirror.target_chat_ids
            
            chat = await self.chat_repo.create(
                chat_id=chat_id,
                title=chat_info["title"],
                username=chat_info["username"],
                chat_type=chat_info["chat_type"],
                description=chat_info["description"],
                is_source=is_source,
                is_target=is_target,
            )
            logger.info(f"Created new chat: {chat}")
        else:
            # Update chat info if needed
            await self.chat_repo.update_info(
                chat_id=chat_id,
                title=chat_info["title"],
                username=chat_info["username"],
                description=chat_info["description"],
            )
        
        return chat
    
    async def create_message_record(
        self,
        message_content: dict,
        media_info: dict,
        forward_info: dict,
        user: Optional[User],
        chat: Chat,
    ) -> Message:
        """Create a message record in the database."""
        
        message = await self.message_repo.create(
            telegram_id=message_content["telegram_id"],
            chat_id=chat.id,
            user_id=user.id if user else None,
            text=message_content["text"],
            media_type=media_info["media_type"],
            media_file_id=media_info["media_file_id"],
            media_file_unique_id=media_info["media_file_unique_id"],
            reply_to_message_id=message_content["reply_to_message_id"],
            message_thread_id=message_content["message_thread_id"],
            is_forwarded=forward_info["is_forwarded"],
            forward_from_user_id=forward_info["forward_from_user_id"],
            forward_from_chat_id=forward_info["forward_from_chat_id"],
        )
        
        logger.info(f"Created message record: {message}")
        return message
    
    async def handle_message_mirroring(
        self, 
        message: Message,
        mirrors: Sequence[Mirror]
    ) -> None:
        """Handle mirroring of a message to target chats."""
        
        for mirror in mirrors:
            try:
                await self.mirror_message_to_target(message, mirror)
            except Exception as e:
                logger.exception(f"Error mirroring message {message.id} to {mirror.target_chat_id}")
    
    async def mirror_message_to_target(
        self,
        message: Message, 
        mirror: Mirror
    ) -> None:
        """Mirror a message to a specific target chat."""
        
        # If rendering is enabled, render the message as an image
        rendered_image_path = None
        if mirror.render_as_image and self.settings.mirror.render_images:
            rendered_image_path = await self.renderer.render_message_as_image(
                message,
                include_media=mirror.include_media,
                include_replies=mirror.include_replies,
            )
        
        # Mark message as mirrored
        await self.message_repo.mark_as_mirrored(
            message.id,
            rendered_image_path=rendered_image_path
        )
        
        logger.info(
            f"Message {message.id} prepared for mirroring to "
            f"chat {mirror.target_chat_id}"
            f"{f' (topic {mirror.target_topic_id})' if mirror.target_topic_id else ''}"
            f"{f' as image: {rendered_image_path}' if rendered_image_path else ''}"
        ) 