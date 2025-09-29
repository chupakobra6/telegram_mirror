"""HTML generation for message rendering."""

import logging
from typing import Optional

from database.models import Message

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """Generator for HTML content from Telegram messages."""
    
    def __init__(self):
        pass
    
    async def generate_message_html(
        self,
        message: Message,
        include_media: bool = True,
        include_replies: bool = True,
    ) -> str:
        """Generate HTML content for a message."""
        
        # User info
        user_display = self._get_user_display_name(message)
        
        # Chat info
        chat_display = self._get_chat_display_name(message)
        
        # Message time
        message_time = message.created_at.strftime("%H:%M:%S")
        
        # Message content
        content_html = ""
        
        # Reply context
        if include_replies and message.reply_to_message_id:
            content_html += self._generate_reply_html(message)
        
        # Forwarded message context
        if message.is_forwarded:
            content_html += self._generate_forward_html(message)
        
        # Message text
        if message.text:
            content_html += f'<div class="message-text">{self._escape_html(message.text)}</div>'
        
        # Media placeholder
        if include_media and message.media_type:
            content_html += self._generate_media_html(message)
        
        # Complete HTML structure
        html = f"""
        <div class="message-container">
            <div class="message-header">
                <div class="chat-name">{self._escape_html(chat_display)}</div>
                <div class="message-time">{message_time}</div>
            </div>
            <div class="user-info">
                <div class="user-name">{self._escape_html(user_display)}</div>
            </div>
            <div class="message-content">
                {content_html}
            </div>
        </div>
        """
        
        return html
    
    def _get_user_display_name(self, message: Message) -> str:
        """Get display name for message user."""
        user_display = "Unknown User"
        if message.user:
            if message.user.first_name:
                user_display = message.user.first_name
                if message.user.last_name:
                    user_display += f" {message.user.last_name}"
            elif message.user.username:
                user_display = f"@{message.user.username}"
        
        return user_display
    
    def _get_chat_display_name(self, message: Message) -> str:
        """Get display name for message chat."""
        return message.chat.title or message.chat.username or "Unknown Chat"
    
    def _generate_reply_html(self, message: Message) -> str:
        """Generate HTML for reply context."""
        return f"""
        <div class="reply-context">
            <div class="reply-indicator">↳ Reply to message #{message.reply_to_message_id}</div>
        </div>
        """
    
    def _generate_forward_html(self, message: Message) -> str:
        """Generate HTML for forwarded message context."""
        forward_from = "Unknown"
        if message.forward_from_user_id:
            forward_from = f"User {message.forward_from_user_id}"
        elif message.forward_from_chat_id:
            forward_from = f"Chat {message.forward_from_chat_id}"
        
        return f"""
        <div class="forward-context">
            <div class="forward-indicator">📤 Forwarded from {self._escape_html(forward_from)}</div>
        </div>
        """
    
    def _generate_media_html(self, message: Message) -> str:
        """Generate HTML for media content."""
        media_type = message.media_type or "Unknown"
        return f"""
        <div class="media-placeholder">
            <div class="media-icon">📎</div>
            <div class="media-type">{media_type.title()}</div>
        </div>
        """
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text."""
        if not text:
            return ""
        
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#x27;")) 