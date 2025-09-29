"""Settings manager for dynamic configuration changes."""

import logging
import os
from typing import Dict, Any

from config import get_settings

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages dynamic configuration changes."""
    
    def __init__(self):
        self.settings = get_settings()
        self._env_file_path = ".env"
    
    def toggle_render_images(self) -> bool:
        """Toggle image rendering setting."""
        try:
            current_value = self.settings.mirror.render_images
            new_value = not current_value
            
            # Update in memory
            self.settings.mirror.render_images = new_value
            
            # Update .env file
            self._update_env_var("MIRROR__RENDER_IMAGES", str(new_value).lower())
            
            logger.info(f"Render images setting changed: {current_value} -> {new_value}")
            return new_value
            
        except Exception as e:
            logger.exception("Error toggling render images setting")
            return self.settings.mirror.render_images
    
    def set_image_size(self, width: int, height: int) -> tuple[int, int]:
        """Set image dimensions."""
        try:
            # Update in memory
            self.settings.mirror.max_image_width = width
            self.settings.mirror.max_image_height = height
            
            # Update .env file
            self._update_env_var("MIRROR__MAX_IMAGE_WIDTH", str(width))
            self._update_env_var("MIRROR__MAX_IMAGE_HEIGHT", str(height))
            
            logger.info(f"Image size changed to: {width}x{height}")
            return width, height
            
        except Exception as e:
            logger.exception("Error setting image size")
            return self.settings.mirror.max_image_width, self.settings.mirror.max_image_height
    
    def set_font_family(self, font_family: str) -> str:
        """Set font family."""
        try:
            # Update in memory
            self.settings.render.font_family = font_family
            
            # Update .env file
            self._update_env_var("RENDER__FONT_FAMILY", font_family)
            
            logger.info(f"Font family changed to: {font_family}")
            return font_family
            
        except Exception as e:
            logger.exception("Error setting font family")
            return self.settings.render.font_family
    
    def set_font_size(self, font_size: int) -> int:
        """Set font size."""
        try:
            # Update in memory
            self.settings.render.font_size = font_size
            
            # Update .env file
            self._update_env_var("RENDER__FONT_SIZE", str(font_size))
            
            logger.info(f"Font size changed to: {font_size}px")
            return font_size
            
        except Exception as e:
            logger.exception("Error setting font size")
            return self.settings.render.font_size
    
    def set_text_color(self, color: str) -> str:
        """Set text color."""
        try:
            # Update in memory
            self.settings.render.text_color = color
            
            # Update .env file  
            self._update_env_var("RENDER__TEXT_COLOR", color)
            
            logger.info(f"Text color changed to: {color}")
            return color
            
        except Exception as e:
            logger.exception("Error setting text color")
            return self.settings.render.text_color
    
    def set_background_color(self, color: str) -> str:
        """Set background color."""
        try:
            # Update in memory
            self.settings.render.background_color = color
            
            # Update .env file
            self._update_env_var("RENDER__BACKGROUND_COLOR", color)
            
            logger.info(f"Background color changed to: {color}")
            return color
            
        except Exception as e:
            logger.exception("Error setting background color")
            return self.settings.render.background_color
    
    def set_log_level(self, level: str) -> str:
        """Set logging level."""
        try:
            # Update in memory
            self.settings.logging.level = level.upper()
            
            # Update .env file
            self._update_env_var("LOGGING__LEVEL", level.upper())
            
            # Update current logger level
            level_map = {
                'CRITICAL': logging.CRITICAL,
                'ERROR': logging.ERROR,
                'WARNING': logging.WARNING,
                'INFO': logging.INFO,
                'DEBUG': logging.DEBUG,
                'NOTSET': logging.NOTSET,
            }
            logging.getLogger().setLevel(level_map.get(level.upper(), logging.INFO))
            
            logger.info(f"Log level changed to: {level.upper()}")
            return level.upper()
            
        except Exception as e:
            logger.exception("Error setting log level")
            return self.settings.logging.level
    
    def _update_env_var(self, key: str, value: str) -> None:
        """Update environment variable in .env file."""
        try:
            if not os.path.exists(self._env_file_path):
                logger.warning(f".env file not found: {self._env_file_path}")
                return
            
            # Read current content
            with open(self._env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find and update the line
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated = True
                    break
            
            # If not found, add new line
            if not updated:
                lines.append(f"{key}={value}\n")
            
            # Write back
            with open(self._env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            logger.debug(f"Updated .env: {key}={value}")
            
        except Exception as e:
            logger.exception(f"Error updating .env file for {key}={value}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary."""
        return {
            "render_images": self.settings.mirror.render_images,
            "image_width": self.settings.mirror.max_image_width,
            "image_height": self.settings.mirror.max_image_height,
            "font_family": self.settings.render.font_family,
            "font_size": self.settings.render.font_size,
            "text_color": self.settings.render.text_color,
            "background_color": self.settings.render.background_color,
            "log_level": self.settings.logging.level,
        } 