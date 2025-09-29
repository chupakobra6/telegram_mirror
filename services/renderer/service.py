"""Message rendering service for converting Telegram messages to images."""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from html2image import Html2Image

from config import get_settings
from database.models import Message
from .css_styles import CSSStylesGenerator
from .html_generator import HTMLGenerator

logger = logging.getLogger(__name__)


class MessageRenderer:
    """Service for rendering Telegram messages as images."""
    
    def __init__(self):
        self.settings = get_settings()
        self.render_settings = self.settings.render
        self.output_dir = Path("rendered_messages")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.html_generator = HTMLGenerator()
        self.css_generator = CSSStylesGenerator()
        
        # Initialize HTML to image converter
        self.hti = Html2Image(
            output_path=str(self.output_dir),
            size=(self.settings.mirror.max_image_width, None)
        )
    
    async def render_message_as_image(
        self, 
        message: Message,
        include_media: bool = True,
        include_replies: bool = True,
    ) -> Optional[str]:
        """Render a Telegram message as an image.
        
        Args:
            message: The message to render
            include_media: Whether to include media in the render
            include_replies: Whether to include reply context
            
        Returns:
            Path to the rendered image file, or None if rendering failed
        """
        try:
            # Generate HTML content
            html_content = await self.html_generator.generate_message_html(
                message, include_media, include_replies
            )
            
            # Generate CSS styles
            css_styles = self.css_generator.get_complete_styles()
            
            # Generate filename
            filename = f"message_{message.chat_id}_{message.telegram_id}_{message.id}.png"
            
            # Render HTML to image
            self.hti.screenshot(
                html_str=html_content,
                save_as=filename,
                css_str=css_styles,
            )
            
            image_path = self.output_dir / filename
            if image_path.exists():
                logger.info(f"Message rendered successfully: {image_path}")
                return str(image_path)
            else:
                logger.error(f"Failed to render message: {filename}")
                return None
                
        except Exception as e:
            logger.exception(f"Error rendering message {message.id} as image")
            return None
    
    async def cleanup_old_renders(self, days_old: int = 7) -> None:
        """Clean up old rendered message files.
        
        Args:
            days_old: Number of days after which to delete files
        """
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            deleted_count = 0
            for file_path in self.output_dir.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old render: {file_path}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old rendered files")
                    
        except Exception as e:
            logger.exception("Error cleaning up old rendered files")
    
    def get_output_directory(self) -> Path:
        """Get the output directory for rendered images."""
        return self.output_dir
    
    def get_render_stats(self) -> dict:
        """Get statistics about rendered files."""
        try:
            files = list(self.output_dir.glob("*.png"))
            total_files = len(files)
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "output_directory": str(self.output_dir),
            }
        except Exception as e:
            logger.exception("Error getting render stats")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "output_directory": str(self.output_dir),
                "error": str(e),
            } 