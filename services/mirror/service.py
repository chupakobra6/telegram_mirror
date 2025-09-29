"""Mirror service for handling message mirroring logic."""

import logging
from typing import Optional, Sequence

from pyrogram.types import Message as PyrogramMessage
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database.models import Message, Mirror
from database.repositories import MirrorRepository
from .handlers import MirrorHandler
from .processors import MessageProcessor

logger = logging.getLogger(__name__)


class MirrorService:
    """Service for handling message mirroring operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        
        # Initialize components
        self.mirror_repo = MirrorRepository(session)
        self.handler = MirrorHandler(session)
        self.processor = MessageProcessor()
    
    async def process_incoming_message(
        self, 
        pyrogram_message: PyrogramMessage
    ) -> Optional[Message]:
        """Process an incoming Telegram message.
        
        Args:
            pyrogram_message: The pyrogram message object
            
        Returns:
            The created/updated Message object, or None if processing failed
        """
        try:
            # Extract information from pyrogram message
            user_info = self.processor.extract_user_info(pyrogram_message)
            chat_info = self.processor.extract_chat_info(pyrogram_message)
            media_info = self.processor.extract_media_info(pyrogram_message)
            forward_info = self.processor.extract_forward_info(pyrogram_message)
            message_content = self.processor.extract_message_content(pyrogram_message)
            
            # Ensure user and chat exist
            user = await self.handler.ensure_user_exists(user_info)
            chat = await self.handler.ensure_chat_exists(chat_info)
            
            # Create message record
            message = await self.handler.create_message_record(
                message_content, media_info, forward_info, user, chat
            )
            
            # Check if this message should be mirrored
            mirrors = await self.mirror_repo.get_by_source_chat(chat.id)
            if mirrors:
                await self.handler.handle_message_mirroring(message, mirrors)
            
            await self.session.commit()
            return message
            
        except Exception as e:
            logger.exception(f"Error processing incoming message {pyrogram_message.id}")
            await self.session.rollback()
            return None
    
    async def create_mirror_configuration(
        self,
        source_chat_id: int,
        target_chat_id: int,
        target_topic_id: Optional[int] = None,
        render_as_image: bool = True,
        include_media: bool = True,
        include_replies: bool = True,
    ) -> Optional[Mirror]:
        """Create a new mirror configuration.
        
        Args:
            source_chat_id: ID of the source chat to mirror from
            target_chat_id: ID of the target chat to mirror to
            target_topic_id: Optional topic ID in the target chat
            render_as_image: Whether to render messages as images
            include_media: Whether to include media in mirroring
            include_replies: Whether to include reply context
            
        Returns:
            The created Mirror object, or None if creation failed
        """
        try:
            # Ensure both chats exist
            from database.repositories import ChatRepository
            chat_repo = ChatRepository(self.session)
            
            source_chat = await chat_repo.get_by_id(source_chat_id)
            if not source_chat:
                logger.error(f"Source chat {source_chat_id} does not exist")
                return None
            
            target_chat = await chat_repo.get_by_id(target_chat_id)
            if not target_chat:
                logger.error(f"Target chat {target_chat_id} does not exist")
                return None
            
            # Create mirror configuration
            mirror = await self.mirror_repo.create(
                source_chat_id=source_chat_id,
                target_chat_id=target_chat_id,
                target_topic_id=target_topic_id,
                render_as_image=render_as_image,
                include_media=include_media,
                include_replies=include_replies,
            )
            
            await self.session.commit()
            logger.info(f"Created mirror configuration: {mirror}")
            return mirror
            
        except Exception as e:
            logger.exception("Error creating mirror configuration")
            await self.session.rollback()
            return None
    
    async def get_active_mirrors(self) -> Sequence[Mirror]:
        """Get all active mirror configurations."""
        return await self.mirror_repo.get_active_mirrors()
    
    async def get_mirrors_for_source_chat(self, source_chat_id: int) -> Sequence[Mirror]:
        """Get all mirrors for a specific source chat."""
        return await self.mirror_repo.get_by_source_chat(source_chat_id)
    
    async def delete_mirror(self, mirror_id: int) -> bool:
        """Delete a mirror configuration."""
        try:
            success = await self.mirror_repo.delete_mirror(mirror_id)
            if success:
                await self.session.commit()
                logger.info(f"Deleted mirror configuration {mirror_id}")
            return success
        except Exception as e:
            logger.exception(f"Error deleting mirror {mirror_id}")
            await self.session.rollback()
            return False
    
    async def toggle_mirror(self, mirror_id: int) -> Optional[Mirror]:
        """Toggle a mirror's active status."""
        try:
            mirror = await self.mirror_repo.toggle_active(mirror_id)
            if mirror:
                await self.session.commit()
                logger.info(f"Toggled mirror {mirror_id} active status to {mirror.is_active}")
            return mirror
        except Exception as e:
            logger.exception(f"Error toggling mirror {mirror_id}")
            await self.session.rollback()
            return None 