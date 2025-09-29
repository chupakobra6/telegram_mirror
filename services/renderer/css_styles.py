"""CSS styles for message rendering."""

from config import get_settings


class CSSStylesGenerator:
    """Generator for CSS styles used in message rendering."""
    
    def __init__(self):
        self.settings = get_settings().render
    
    def get_base_styles(self) -> str:
        """Get base CSS styles for message rendering."""
        return f"""
        body {{
            font-family: {self.settings.font_family}, sans-serif;
            font-size: {self.settings.font_size}px;
            margin: 0;
            padding: {self.settings.padding}px;
            background-color: {self.settings.background_color};
            color: {self.settings.text_color};
        }}
        
        .message-container {{
            background: white;
            border-radius: {self.settings.border_radius}px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #0088cc;
        }}
        """
    
    def get_header_styles(self) -> str:
        """Get header styles for message rendering."""
        return """
        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 5px;
        }
        
        .chat-name {
            font-weight: bold;
            color: #0088cc;
            font-size: 12px;
        }
        
        .message-time {
            font-size: 11px;
            color: #666;
        }
        """
    
    def get_user_styles(self) -> str:
        """Get user info styles."""
        return """
        .user-info {
            margin-bottom: 8px;
        }
        
        .user-name {
            font-weight: 600;
            color: #2b5278;
            font-size: 13px;
        }
        """
    
    def get_content_styles(self) -> str:
        """Get content styles."""
        return """
        .message-content {
            line-height: 1.4;
        }
        
        .message-text {
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 8px 0;
        }
        """
    
    def get_context_styles(self) -> str:
        """Get context styles for replies and forwards."""
        return """
        .reply-context, .forward-context {
            background: #f5f5f5;
            border-left: 3px solid #0088cc;
            padding: 6px 10px;
            margin: 5px 0;
            font-size: 11px;
            color: #666;
        }
        """
    
    def get_media_styles(self) -> str:
        """Get media placeholder styles."""
        return """
        .media-placeholder {
            background: #f8f9fa;
            border: 1px dashed #ccc;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
            margin: 8px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .media-icon {
            font-size: 18px;
        }
        
        .media-type {
            font-size: 12px;
            color: #666;
            font-weight: 500;
        }
        """
    
    def get_complete_styles(self) -> str:
        """Get all CSS styles combined."""
        return (
            self.get_base_styles() +
            self.get_header_styles() +
            self.get_user_styles() +
            self.get_content_styles() +
            self.get_context_styles() +
            self.get_media_styles()
        ) 