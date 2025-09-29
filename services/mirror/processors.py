"""Message processors for handling different types of Telegram messages."""

import logging
from typing import Optional, Dict, Any

from pyrogram.types import Message as PyrogramMessage

from database.models import User, Chat

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Base class for processing different types of messages."""
    
    def __init__(self):
        pass
    
    def extract_user_info(self, pyrogram_message: PyrogramMessage) -> Optional[Dict[str, Any]]:
        """Extract user information from pyrogram message."""
        if not pyrogram_message.from_user:
            return None
        
        return {
            "user_id": pyrogram_message.from_user.id,
            "username": pyrogram_message.from_user.username,
            "first_name": pyrogram_message.from_user.first_name,
            "last_name": pyrogram_message.from_user.last_name,
        }
    
    def extract_chat_info(self, pyrogram_message: PyrogramMessage) -> Dict[str, Any]:
        """Extract chat information from pyrogram message."""
        chat_type = pyrogram_message.chat.type.value if pyrogram_message.chat.type else "unknown"
        
        return {
            "chat_id": pyrogram_message.chat.id,
            "title": pyrogram_message.chat.title,
            "username": pyrogram_message.chat.username,
            "chat_type": chat_type,
            "description": pyrogram_message.chat.description,
        }
    
    def extract_media_info(self, pyrogram_message: PyrogramMessage) -> Dict[str, Optional[str]]:
        """Extract media information from pyrogram message."""
        media_type = None
        media_file_id = None
        media_file_unique_id = None
        
        if pyrogram_message.photo:
            media_type = "photo"
            media_file_id = pyrogram_message.photo.file_id
            media_file_unique_id = pyrogram_message.photo.file_unique_id
        elif pyrogram_message.video:
            media_type = "video"
            media_file_id = pyrogram_message.video.file_id
            media_file_unique_id = pyrogram_message.video.file_unique_id
        elif pyrogram_message.document:
            media_type = "document"
            media_file_id = pyrogram_message.document.file_id
            media_file_unique_id = pyrogram_message.document.file_unique_id
        elif pyrogram_message.audio:
            media_type = "audio"
            media_file_id = pyrogram_message.audio.file_id
            media_file_unique_id = pyrogram_message.audio.file_unique_id
        elif pyrogram_message.voice:
            media_type = "voice"
            media_file_id = pyrogram_message.voice.file_id
            media_file_unique_id = pyrogram_message.voice.file_unique_id
        elif pyrogram_message.sticker:
            media_type = "sticker"
            media_file_id = pyrogram_message.sticker.file_id
            media_file_unique_id = pyrogram_message.sticker.file_unique_id
        
        return {
            "media_type": media_type,
            "media_file_id": media_file_id,
            "media_file_unique_id": media_file_unique_id,
        }
    
    def extract_forward_info(self, pyrogram_message: PyrogramMessage) -> Dict[str, Any]:
        """Extract forwarded message information."""
        is_forwarded = pyrogram_message.forward_from or pyrogram_message.forward_from_chat
        forward_from_user_id = None
        forward_from_chat_id = None
        forward_date = None
        
        if is_forwarded:
            if pyrogram_message.forward_from:
                forward_from_user_id = pyrogram_message.forward_from.id
            if pyrogram_message.forward_from_chat:
                forward_from_chat_id = pyrogram_message.forward_from_chat.id
            forward_date = pyrogram_message.forward_date
        
        return {
            "is_forwarded": is_forwarded,
            "forward_from_user_id": forward_from_user_id,
            "forward_from_chat_id": forward_from_chat_id,
            "forward_date": forward_date,
        }
    
    def extract_message_content(self, pyrogram_message: PyrogramMessage) -> Dict[str, Any]:
        """Extract message content and metadata."""
        return {
            "telegram_id": pyrogram_message.id,
            "text": pyrogram_message.text or pyrogram_message.caption,
            "reply_to_message_id": pyrogram_message.reply_to_message_id,
            "message_thread_id": pyrogram_message.message_thread_id,
        } 