"""Command handlers for Telegram bot."""

import logging
from typing import Optional

from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_manager
from database.repositories import ChatRepository, MirrorRepository, UserRepository

from .keyboards import *
from .menus import *
from .settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class BotHandlers:
    """Handler class for bot commands and callbacks."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.settings_manager = SettingsManager()
    
    async def handle_start_command(self, message: Message) -> None:
        """Handle /start command."""
        try:
            # Log incoming message
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            logger.info(
                f"📥 Получена команда /start от {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            text = get_main_menu_text()
            keyboard = get_main_menu_keyboard()
            await message.answer(text, reply_markup=keyboard)
            
            logger.info(f"📤 Отправлено главное меню пользователю {user_name} (ID: {message.from_user.id})")
        except Exception as e:
            logger.exception("Error in start command")
            await message.answer("❌ Произошла ошибка при загрузке главного меню")
    
    async def handle_settings_command(self, message: Message) -> None:
        """Handle /settings command."""
        try:
            # Log incoming message
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            logger.info(
                f"📥 Получена команда /settings от {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            from config import get_settings
            settings = get_settings()
            text = get_settings_menu_text()
            keyboard = get_settings_keyboard(render_enabled=settings.mirror.render_images)
            await message.answer(text, reply_markup=keyboard)
            
            logger.info(f"📤 Отправлено меню настроек пользователю {user_name} (ID: {message.from_user.id})")
        except Exception as e:
            logger.exception("Error in settings command")
            await message.answer("❌ Произошла ошибка при загрузке настроек")
    
    async def handle_mirrors_command(self, message: Message) -> None:
        """Handle /mirrors command."""
        try:
            # Log incoming message
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            logger.info(
                f"📥 Получена команда /mirrors от {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            async with self.db_manager.get_session() as session:
                mirror_repo = MirrorRepository(session)
                mirrors = await mirror_repo.get_active_mirrors()
            
            text = get_mirrors_menu_text(len(mirrors))
            keyboard = get_mirror_list_keyboard(mirrors)
            await message.answer(text, reply_markup=keyboard)
            
            logger.info(f"📤 Отправлено меню зеркал пользователю {user_name} (ID: {message.from_user.id})")
        except Exception as e:
            logger.exception("Error in mirrors command")
            await message.answer("❌ Произошла ошибка при загрузке зеркал")
    
    async def handle_chats_command(self, message: Message) -> None:
        """Handle /chats command."""
        try:
            # Log incoming message
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            logger.info(
                f"📥 Получена команда /chats от {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            async with self.db_manager.get_session() as session:
                chat_repo = ChatRepository(session)
                source_chats = await chat_repo.get_source_chats()
                target_chats = await chat_repo.get_target_chats()
            
            text = get_chats_menu_text(len(source_chats), len(target_chats))
            keyboard = get_chats_keyboard()
            await message.answer(text, reply_markup=keyboard)
            
            logger.info(f"📤 Отправлено меню чатов пользователю {user_name} (ID: {message.from_user.id})")
        except Exception as e:
            logger.exception("Error in chats command")
            await message.answer("❌ Произошла ошибка при загрузке чатов")
    
    async def handle_users_command(self, message: Message) -> None:
        """Handle /users command."""
        try:
            # Log incoming message
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            logger.info(
                f"📥 Получена команда /users от {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            async with self.db_manager.get_session() as session:
                user_repo = UserRepository(session)
                admins = await user_repo.get_admins()
                allowed_users = await user_repo.get_allowed_users()
            
            text = get_users_menu_text(len(admins), len(allowed_users))
            keyboard = get_users_keyboard()
            await message.answer(text, reply_markup=keyboard)
            
            logger.info(f"📤 Отправлено меню пользователей пользователю {user_name} (ID: {message.from_user.id})")
        except Exception as e:
            logger.exception("Error in users command")
            await message.answer("❌ Произошла ошибка при загрузке пользователей")
    
    async def handle_stats_command(self, message: Message) -> None:
        """Handle /stats command."""
        try:
            # Log incoming message
            user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
            username = message.from_user.username
            logger.info(
                f"📥 Получена команда /stats от {user_name} (@{username or 'no_username'}, ID: {message.from_user.id})"
            )
            
            async with self.db_manager.get_session() as session:
                mirror_repo = MirrorRepository(session)
                chat_repo = ChatRepository(session)
                user_repo = UserRepository(session)
                
                mirrors = await mirror_repo.get_active_mirrors()
                chats = await chat_repo.get_source_chats()
                users = await user_repo.get_allowed_users()
            
            text = get_stats_menu_text(len(mirrors), len(chats), len(users))
            keyboard = get_stats_keyboard()
            await message.answer(text, reply_markup=keyboard)
            
            logger.info(f"📤 Отправлена статистика пользователю {user_name} (ID: {message.from_user.id})")
        except Exception as e:
            logger.exception("Error in stats command")
            await message.answer("❌ Произошла ошибка при загрузке статистики")
    
    async def handle_callback_query(self, callback: CallbackQuery) -> None:
        """Handle callback queries from inline keyboards."""
        if not callback.data:
            await callback.answer("❌ Неверные данные")
            return
        
        try:
            # Log callback query
            user_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
            username = callback.from_user.username
            logger.info(
                f"📥 Callback query '{callback.data}' от {user_name} (@{username or 'no_username'}, ID: {callback.from_user.id})"
            )
            
            data = callback.data
            
            # Main menu callbacks
            if data == "main_menu":
                await self._show_main_menu(callback)
            elif data == "settings":
                await self._show_settings_menu(callback)
            elif data == "mirrors":
                await self._show_mirrors_menu(callback)
            elif data == "chats":
                await self._show_chats_menu(callback)
            elif data == "users":
                await self._show_users_menu(callback)
            elif data == "stats":
                await self._show_stats_menu(callback)
            elif data == "help":
                await self._show_help_menu(callback)
            
            # Settings callbacks
            elif data == "toggle_render":
                await self._toggle_render_setting(callback)
            elif data == "image_size":
                await self._show_image_size_menu(callback)
            elif data == "font_settings":
                await self._show_font_settings_menu(callback)
            elif data == "log_level":
                await self._show_log_level_menu(callback)
            
            # Image size callbacks
            elif data.startswith("size_"):
                await self._set_image_size(callback, data)
            
            # Font callbacks
            elif data == "font_family":
                await self._show_font_family_menu(callback)
            elif data == "font_size": 
                await self._show_font_size_menu(callback)
            elif data.startswith("font_"):
                await self._set_font_family(callback, data)
            elif data.startswith("fontsize_"):
                await self._set_font_size(callback, data)
            elif data in ["text_color", "bg_color"]:
                await callback.answer("🎨 Выбор цвета через цветовую палитру пока не реализован")
            
            # Log level callbacks
            elif data.startswith("loglevel_"):
                await self._set_log_level(callback, data)
            
            # Mirrors callbacks
            elif data == "mirror_add":
                await self._show_add_mirror_menu(callback)
            elif data.startswith("mirror_view_"):
                mirror_id = data.split("_")[2]
                await self._show_mirror_details(callback, mirror_id)
            
            # Chats callbacks
            elif data == "chat_sources":
                await self._show_chat_sources(callback)
            elif data == "chat_targets":
                await self._show_chat_targets(callback)
            elif data == "chat_add":
                await self._show_add_chat_menu(callback)
            elif data.startswith("chat_source_") or data.startswith("chat_target_"):
                chat_id = data.split("_")[2]
                await self._show_chat_details(callback, chat_id)
            
            # Users callbacks
            elif data == "user_admins":
                await self._show_user_admins(callback)
            elif data == "user_allowed":
                await self._show_user_allowed(callback)
            elif data == "user_add":
                await self._show_add_user_menu(callback)
            elif data.startswith("user_admin_") or data.startswith("user_allowed_"):
                user_id = data.split("_")[2]
                await self._show_user_details(callback, user_id)
            
            # Stats callbacks
            elif data == "stats_detailed":
                await callback.answer("📊 Подробная статистика в разработке")
            
            # General callbacks
            elif data == "cancel":
                await callback.answer("❌ Операция отменена")
            
            else:
                await callback.answer("❌ Неизвестная команда")
                logger.warning(f"Unknown callback data: {data}")
            
        except Exception as e:
            logger.exception(f"Error handling callback: {callback.data}")
            await callback.answer("❌ Произошла ошибка")
    
    async def _show_main_menu(self, callback: CallbackQuery) -> None:
        """Show main menu."""
        text = get_main_menu_text()
        keyboard = get_main_menu_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_settings_menu(self, callback: CallbackQuery) -> None:
        """Show settings menu."""
        from config import get_settings
        settings = get_settings()
        text = get_settings_menu_text()
        keyboard = get_settings_keyboard(render_enabled=settings.mirror.render_images)
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_mirrors_menu(self, callback: CallbackQuery) -> None:
        """Show mirrors menu."""
        async with self.db_manager.get_session() as session:
            mirror_repo = MirrorRepository(session)
            mirrors = await mirror_repo.get_active_mirrors()
        
        text = get_mirrors_menu_text(len(mirrors))
        keyboard = get_mirror_list_keyboard(mirrors)
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_chats_menu(self, callback: CallbackQuery) -> None:
        """Show chats menu."""
        async with self.db_manager.get_session() as session:
            chat_repo = ChatRepository(session)
            source_chats = await chat_repo.get_source_chats()
            target_chats = await chat_repo.get_target_chats()
        
        text = get_chats_menu_text(len(source_chats), len(target_chats))
        keyboard = get_chats_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_users_menu(self, callback: CallbackQuery) -> None:
        """Show users menu."""
        async with self.db_manager.get_session() as session:
            user_repo = UserRepository(session)
            admins = await user_repo.get_admins()
            allowed_users = await user_repo.get_allowed_users()
        
        text = get_users_menu_text(len(admins), len(allowed_users))
        keyboard = get_users_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_stats_menu(self, callback: CallbackQuery) -> None:
        """Show stats menu."""
        async with self.db_manager.get_session() as session:
            mirror_repo = MirrorRepository(session)
            chat_repo = ChatRepository(session)
            user_repo = UserRepository(session)
            
            mirrors = await mirror_repo.get_active_mirrors()
            chats = await chat_repo.get_source_chats()
            users = await user_repo.get_allowed_users()
        
        text = get_stats_menu_text(len(mirrors), len(chats), len(users))
        keyboard = get_stats_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_help_menu(self, callback: CallbackQuery) -> None:
        """Show help menu."""
        text = get_help_menu_text()
        keyboard = get_help_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _toggle_render_setting(self, callback: CallbackQuery) -> None:
        """Toggle render setting."""
        try:
            new_value = self.settings_manager.toggle_render_images()
            await callback.answer(f"🖼️ Рендеринг {'включен' if new_value else 'отключен'}")
            # Refresh settings menu
            await self._show_settings_menu(callback)
        except Exception as e:
            logger.exception("Error toggling render setting")
            await callback.answer("❌ Ошибка изменения настройки")
    
    async def _show_add_mirror_menu(self, callback: CallbackQuery) -> None:
        """Show add mirror instructions."""
        text = get_add_mirror_text()
        keyboard = get_mirrors_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_mirror_details(self, callback: CallbackQuery, mirror_id: str) -> None:
        """Show mirror details."""
        # TODO: Implement mirror details
        await callback.answer(f"🔄 Детали зеркала {mirror_id} в разработке")
    
    async def _show_chat_sources(self, callback: CallbackQuery) -> None:
        """Show source chats."""
        async with self.db_manager.get_session() as session:
            chat_repo = ChatRepository(session)
            chats = await chat_repo.get_source_chats()
        
        text = f"📤 <b>Чаты-источники ({len(chats)})</b>\n\nВыберите чат для просмотра деталей:"
        keyboard = get_chat_sources_keyboard(chats)
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_chat_targets(self, callback: CallbackQuery) -> None:
        """Show target chats."""
        async with self.db_manager.get_session() as session:
            chat_repo = ChatRepository(session)
            chats = await chat_repo.get_target_chats()
        
        text = f"📥 <b>Чаты-назначения ({len(chats)})</b>\n\nВыберите чат для просмотра деталей:"
        keyboard = get_chat_targets_keyboard(chats)
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_add_chat_menu(self, callback: CallbackQuery) -> None:
        """Show add chat instructions."""
        text = get_add_chat_text()
        keyboard = get_chats_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_chat_details(self, callback: CallbackQuery, chat_id: str) -> None:
        """Show chat details."""
        # TODO: Implement chat details
        await callback.answer(f"💬 Детали чата {chat_id} в разработке")
    
    async def _show_user_admins(self, callback: CallbackQuery) -> None:
        """Show admin users."""
        async with self.db_manager.get_session() as session:
            user_repo = UserRepository(session)
            users = await user_repo.get_admins()
        
        text = f"👑 <b>Администраторы ({len(users)})</b>\n\nВыберите пользователя для управления:"
        keyboard = get_user_admins_keyboard(users)
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_user_allowed(self, callback: CallbackQuery) -> None:
        """Show allowed users."""
        async with self.db_manager.get_session() as session:
            user_repo = UserRepository(session)
            users = await user_repo.get_allowed_users()
        
        text = f"✅ <b>Разрешенные пользователи ({len(users)})</b>\n\nВыберите пользователя для управления:"
        keyboard = get_user_allowed_keyboard(users)
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_add_user_menu(self, callback: CallbackQuery) -> None:
        """Show add user instructions."""
        text = get_add_user_text()
        keyboard = get_users_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_user_details(self, callback: CallbackQuery, user_id: str) -> None:
        """Show user details."""
        # TODO: Implement user details
        await callback.answer(f"👤 Детали пользователя {user_id} в разработке")
    
    async def _show_image_size_menu(self, callback: CallbackQuery) -> None:
        """Show image size selection menu."""
        settings = self.settings_manager.get_current_settings()
        text = f"""
📐 <b>Размер изображений</b>

Текущий размер: <b>{settings['image_width']}x{settings['image_height']}</b>

Выберите новый размер:
        """
        keyboard = get_image_size_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _set_image_size(self, callback: CallbackQuery, data: str) -> None:
        """Set image size from callback data."""
        try:
            # Parse size from callback data: "size_800_600"
            parts = data.split("_")
            width, height = int(parts[1]), int(parts[2])
            
            self.settings_manager.set_image_size(width, height)
            await callback.answer(f"📐 Размер изменен на {width}x{height}")
            await self._show_image_size_menu(callback)
            
        except Exception as e:
            logger.exception("Error setting image size")
            await callback.answer("❌ Ошибка изменения размера")
    
    async def _show_font_settings_menu(self, callback: CallbackQuery) -> None:
        """Show font settings menu."""
        settings = self.settings_manager.get_current_settings()
        text = f"""
🎨 <b>Настройки шрифта</b>

📝 <b>Шрифт:</b> {settings['font_family']}
📏 <b>Размер:</b> {settings['font_size']}px
🎨 <b>Цвет текста:</b> {settings['text_color']}
🖼️ <b>Цвет фона:</b> {settings['background_color']}

Выберите параметр для изменения:
        """
        keyboard = get_font_settings_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _show_font_family_menu(self, callback: CallbackQuery) -> None:
        """Show font family selection menu."""
        settings = self.settings_manager.get_current_settings()
        text = f"""
🔤 <b>Выбор шрифта</b>

Текущий шрифт: <b>{settings['font_family']}</b>

Выберите новый шрифт:
        """
        keyboard = get_font_family_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _set_font_family(self, callback: CallbackQuery, data: str) -> None:
        """Set font family from callback data."""
        try:
            # Parse font from callback data: "font_Arial"
            font_family = data.replace("font_", "").replace("Times", "Times New Roman").replace("Courier", "Courier New")
            
            self.settings_manager.set_font_family(font_family)
            await callback.answer(f"🔤 Шрифт изменен на {font_family}")
            await self._show_font_family_menu(callback)
            
        except Exception as e:
            logger.exception("Error setting font family")
            await callback.answer("❌ Ошибка изменения шрифта")
    
    async def _show_font_size_menu(self, callback: CallbackQuery) -> None:
        """Show font size selection menu."""
        settings = self.settings_manager.get_current_settings()
        text = f"""
📏 <b>Размер шрифта</b>

Текущий размер: <b>{settings['font_size']}px</b>

Выберите новый размер:
        """
        keyboard = get_font_size_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _set_font_size(self, callback: CallbackQuery, data: str) -> None:
        """Set font size from callback data."""
        try:
            # Parse size from callback data: "fontsize_14"
            font_size = int(data.replace("fontsize_", ""))
            
            self.settings_manager.set_font_size(font_size)
            await callback.answer(f"📏 Размер шрифта изменен на {font_size}px")
            await self._show_font_size_menu(callback)
            
        except Exception as e:
            logger.exception("Error setting font size")
            await callback.answer("❌ Ошибка изменения размера шрифта")
    
    async def _show_log_level_menu(self, callback: CallbackQuery) -> None:
        """Show log level selection menu."""
        settings = self.settings_manager.get_current_settings()
        text = f"""
📝 <b>Уровень логирования</b>

Текущий уровень: <b>{settings['log_level']}</b>

Выберите новый уровень:
• ERROR - только критические ошибки
• WARNING - предупреждения и ошибки
• INFO - информация, предупреждения и ошибки
• DEBUG - вся отладочная информация
        """
        keyboard = get_log_level_keyboard()
        await self._safe_edit_message(callback, text, keyboard)
    
    async def _set_log_level(self, callback: CallbackQuery, data: str) -> None:
        """Set log level from callback data."""
        try:
            # Parse level from callback data: "loglevel_INFO"
            log_level = data.replace("loglevel_", "")
            
            self.settings_manager.set_log_level(log_level)
            await callback.answer(f"📝 Уровень логов изменен на {log_level}")
            await self._show_log_level_menu(callback)
            
        except Exception as e:
            logger.exception("Error setting log level")
            await callback.answer("❌ Ошибка изменения уровня логов")
    
    async def _safe_edit_message(self, callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup) -> None:
        """Safely edit message, avoiding 'message not modified' errors."""
        try:
            if callback.message:
                # Check if content would be the same
                current_text = callback.message.text or callback.message.caption or ""
                if current_text.strip() != text.strip():
                    await callback.message.edit_text(text, reply_markup=keyboard)
                    await callback.answer()
                else:
                    # Content is the same, just answer the callback
                    await callback.answer("✅ Меню обновлено")
            else:
                await callback.answer("❌ Не удалось обновить сообщение")
        except Exception as e:
            logger.exception("Error editing message")
            try:
                await callback.answer("❌ Ошибка обновления сообщения")
            except:
                pass 