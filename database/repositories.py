"""Repository classes for database operations."""

import logging
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Chat, Message, Mirror, User

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session


class UserRepository(BaseRepository):
    """Repository for User operations."""
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_admin: bool = False,
        is_allowed: bool = False,
    ) -> User:
        """Create a new user."""
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            is_allowed=is_allowed,
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def update_permissions(
        self, 
        user_id: int, 
        is_admin: bool | None = None,
        is_allowed: bool | None = None,
    ) -> Optional[User]:
        """Update user permissions."""
        updates = {}
        if is_admin is not None:
            updates["is_admin"] = is_admin
        if is_allowed is not None:
            updates["is_allowed"] = is_allowed
        
        if not updates:
            return await self.get_by_id(user_id)
        
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**updates)
        )
        return await self.get_by_id(user_id)
    
    async def get_admins(self) -> Sequence[User]:
        """Get all admin users."""
        result = await self.session.execute(
            select(User).where(User.is_admin == True).where(User.is_active == True)
        )
        return result.scalars().all()
    
    async def get_allowed_users(self) -> Sequence[User]:
        """Get all allowed users."""
        result = await self.session.execute(
            select(User).where(User.is_allowed == True).where(User.is_active == True)
        )
        return result.scalars().all()


class ChatRepository(BaseRepository):
    """Repository for Chat operations."""
    
    async def get_by_id(self, chat_id: int) -> Optional[Chat]:
        """Get chat by Telegram ID."""
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[Chat]:
        """Get chat by username."""
        result = await self.session.execute(
            select(Chat).where(Chat.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        chat_id: int,
        title: str | None = None,
        username: str | None = None,
        chat_type: str = "unknown",
        description: str | None = None,
        is_source: bool = False,
        is_target: bool = False,
    ) -> Chat:
        """Create a new chat."""
        chat = Chat(
            id=chat_id,
            title=title,
            username=username,
            type=chat_type,
            description=description,
            is_source=is_source,
            is_target=is_target,
        )
        self.session.add(chat)
        await self.session.flush()
        return chat
    
    async def update_info(
        self,
        chat_id: int,
        title: str | None = None,
        username: str | None = None,
        description: str | None = None,
    ) -> Optional[Chat]:
        """Update chat information."""
        updates = {}
        if title is not None:
            updates["title"] = title
        if username is not None:
            updates["username"] = username
        if description is not None:
            updates["description"] = description
        
        if not updates:
            return await self.get_by_id(chat_id)
        
        await self.session.execute(
            update(Chat)
            .where(Chat.id == chat_id)
            .values(**updates)
        )
        return await self.get_by_id(chat_id)
    
    async def get_source_chats(self) -> Sequence[Chat]:
        """Get all source chats."""
        result = await self.session.execute(
            select(Chat).where(Chat.is_source == True).where(Chat.is_active == True)
        )
        return result.scalars().all()
    
    async def get_target_chats(self) -> Sequence[Chat]:
        """Get all target chats."""
        result = await self.session.execute(
            select(Chat).where(Chat.is_target == True).where(Chat.is_active == True)
        )
        return result.scalars().all()


class MessageRepository(BaseRepository):
    """Repository for Message operations."""
    
    async def get_by_telegram_id(
        self, 
        telegram_id: int, 
        chat_id: int
    ) -> Optional[Message]:
        """Get message by Telegram message ID and chat ID."""
        result = await self.session.execute(
            select(Message)
            .where(Message.telegram_id == telegram_id)
            .where(Message.chat_id == chat_id)
            .options(selectinload(Message.user), selectinload(Message.chat))
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        telegram_id: int,
        chat_id: int,
        user_id: int | None = None,
        text: str | None = None,
        media_type: str | None = None,
        media_file_id: str | None = None,
        media_file_unique_id: str | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
        is_forwarded: bool = False,
        forward_from_chat_id: int | None = None,
        forward_from_user_id: int | None = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            telegram_id=telegram_id,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            media_type=media_type,
            media_file_id=media_file_id,
            media_file_unique_id=media_file_unique_id,
            reply_to_message_id=reply_to_message_id,
            message_thread_id=message_thread_id,
            is_forwarded=is_forwarded,
            forward_from_chat_id=forward_from_chat_id,
            forward_from_user_id=forward_from_user_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message
    
    async def mark_as_mirrored(
        self, 
        message_id: int,
        rendered_image_path: str | None = None
    ) -> Optional[Message]:
        """Mark message as mirrored."""
        await self.session.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                is_mirrored=True,
                mirror_count=Message.mirror_count + 1,
                rendered_image_path=rendered_image_path,
            )
        )
        return await self.get_by_id(message_id)
    
    async def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID."""
        result = await self.session.execute(
            select(Message)
            .where(Message.id == message_id)
            .options(selectinload(Message.user), selectinload(Message.chat))
        )
        return result.scalar_one_or_none()
    
    async def get_recent_messages(
        self, 
        chat_id: int, 
        limit: int = 50
    ) -> Sequence[Message]:
        """Get recent messages from a chat."""
        result = await self.session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .options(selectinload(Message.user), selectinload(Message.chat))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


class MirrorRepository(BaseRepository):
    """Repository for Mirror operations."""
    
    async def get_by_id(self, mirror_id: int) -> Optional[Mirror]:
        """Get mirror by ID."""
        result = await self.session.execute(
            select(Mirror)
            .where(Mirror.id == mirror_id)
            .options(
                selectinload(Mirror.source_chat),
                selectinload(Mirror.target_chat),
            )
        )
        return result.scalar_one_or_none()
    
    async def create(
        self,
        source_chat_id: int,
        target_chat_id: int,
        target_topic_id: int | None = None,
        render_as_image: bool = True,
        include_media: bool = True,
        include_replies: bool = True,
    ) -> Mirror:
        """Create a new mirror configuration."""
        mirror = Mirror(
            source_chat_id=source_chat_id,
            target_chat_id=target_chat_id,
            target_topic_id=target_topic_id,
            render_as_image=render_as_image,
            include_media=include_media,
            include_replies=include_replies,
        )
        self.session.add(mirror)
        await self.session.flush()
        return mirror
    
    async def get_by_source_chat(self, source_chat_id: int) -> Sequence[Mirror]:
        """Get all mirrors for a source chat."""
        result = await self.session.execute(
            select(Mirror)
            .where(Mirror.source_chat_id == source_chat_id)
            .where(Mirror.is_active == True)
            .options(
                selectinload(Mirror.source_chat),
                selectinload(Mirror.target_chat),
            )
        )
        return result.scalars().all()
    
    async def get_active_mirrors(self) -> Sequence[Mirror]:
        """Get all active mirrors."""
        result = await self.session.execute(
            select(Mirror)
            .where(Mirror.is_active == True)
            .options(
                selectinload(Mirror.source_chat),
                selectinload(Mirror.target_chat),
            )
        )
        return result.scalars().all()
    
    async def delete_mirror(self, mirror_id: int) -> bool:
        """Delete a mirror configuration."""
        result = await self.session.execute(
            delete(Mirror).where(Mirror.id == mirror_id)
        )
        return result.rowcount > 0
    
    async def toggle_active(self, mirror_id: int) -> Optional[Mirror]:
        """Toggle mirror active status."""
        mirror = await self.get_by_id(mirror_id)
        if not mirror:
            return None
        
        await self.session.execute(
            update(Mirror)
            .where(Mirror.id == mirror_id)
            .values(is_active=not mirror.is_active)
        )
        return await self.get_by_id(mirror_id) 