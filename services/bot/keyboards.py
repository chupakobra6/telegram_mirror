"""Keyboard definitions for Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="🔄 Зеркала", callback_data="mirrors")
        ],
        [
            InlineKeyboardButton(text="💬 Чаты", callback_data="chats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="users")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])


def get_settings_keyboard(render_enabled: bool) -> InlineKeyboardMarkup:
    """Get settings menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🖼️ Рендеринг: {'✅' if render_enabled else '❌'}", 
                callback_data="toggle_render"
            )
        ],
        [
            InlineKeyboardButton(text="📐 Размер изображений", callback_data="image_size"),
            InlineKeyboardButton(text="🎨 Стили шрифта", callback_data="font_settings")
        ],
        [
            InlineKeyboardButton(text="📝 Уровень логов", callback_data="log_level"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])


def get_mirrors_keyboard() -> InlineKeyboardMarkup:
    """Get mirrors management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить зеркало", callback_data="mirror_add"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="mirrors")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])


def get_chats_keyboard() -> InlineKeyboardMarkup:
    """Get chats management keyboard.""" 
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Источники", callback_data="chat_sources"),
            InlineKeyboardButton(text="📥 Назначения", callback_data="chat_targets")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить чат", callback_data="chat_add"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="chats")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])


def get_users_keyboard() -> InlineKeyboardMarkup:
    """Get users management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Администраторы", callback_data="user_admins"),
            InlineKeyboardButton(text="✅ Разрешенные", callback_data="user_allowed")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="user_add"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="users")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Get statistics keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Подробная статистика", callback_data="stats_detailed"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Get help keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])


def get_mirror_list_keyboard(mirrors: list) -> InlineKeyboardMarkup:
    """Get keyboard with list of mirrors."""
    builder = InlineKeyboardBuilder()
    
    # Add mirror management buttons
    builder.button(text="➕ Добавить зеркало", callback_data="mirror_add")
    builder.button(text="🔄 Обновить список", callback_data="mirrors")
    
    # Add mirrors list
    for mirror in mirrors[:10]:  # Limit to 10 for UI
        source_title = (mirror.source_chat.title if mirror.source_chat and mirror.source_chat.title else None) or f"Chat {mirror.source_chat_id}"
        target_title = (mirror.target_chat.title if mirror.target_chat and mirror.target_chat.title else None) or f"Chat {mirror.target_chat_id}"
        builder.button(
            text=f"🔄 {source_title[:15]}... → {target_title[:15]}...",
            callback_data=f"mirror_view_{mirror.id}"
        )
    
    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    builder.adjust(2, 2)  # 2 buttons per row for first rows
    
    return builder.as_markup()


def get_chat_sources_keyboard(chats: list) -> InlineKeyboardMarkup:
    """Get keyboard with source chats."""
    builder = InlineKeyboardBuilder()
    
    for chat in chats[:10]:
        title = (chat.title if chat and chat.title else None) or f"Chat {chat.chat_id}"
        builder.button(
            text=f"📤 {title[:25]}...",
            callback_data=f"chat_source_{chat.chat_id}"
        )
    
    builder.button(text="🔙 Чаты", callback_data="chats")
    builder.adjust(1)  # 1 button per row
    
    return builder.as_markup()


def get_chat_targets_keyboard(chats: list) -> InlineKeyboardMarkup:
    """Get keyboard with target chats."""
    builder = InlineKeyboardBuilder()
    
    for chat in chats[:10]:
        title = (chat.title if chat and chat.title else None) or f"Chat {chat.chat_id}"
        builder.button(
            text=f"📥 {title[:25]}...",
            callback_data=f"chat_target_{chat.chat_id}"
        )
    
    builder.button(text="🔙 Чаты", callback_data="chats")
    builder.adjust(1)  # 1 button per row
    
    return builder.as_markup()


def get_user_admins_keyboard(users: list) -> InlineKeyboardMarkup:
    """Get keyboard with admin users."""
    builder = InlineKeyboardBuilder()
    
    for user in users[:10]:
        name = (user.first_name if user and user.first_name else None) or f"User {user.user_id}"
        builder.button(
            text=f"👑 {name[:20]}...",
            callback_data=f"user_admin_{user.user_id}"
        )
    
    builder.button(text="🔙 Пользователи", callback_data="users")
    builder.adjust(1)  # 1 button per row
    
    return builder.as_markup()


def get_user_allowed_keyboard(users: list) -> InlineKeyboardMarkup:
    """Get keyboard with allowed users."""
    builder = InlineKeyboardBuilder()
    
    for user in users[:10]:
        name = (user.first_name if user and user.first_name else None) or f"User {user.user_id}"
        builder.button(
            text=f"✅ {name[:20]}...",
            callback_data=f"user_allowed_{user.user_id}"
        )
    
    builder.button(text="🔙 Пользователи", callback_data="users")
    builder.adjust(1)  # 1 button per row
    
    return builder.as_markup()


def get_confirmation_keyboard(action: str, item_id: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard for actions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
        ]
    ])


def get_image_size_keyboard() -> InlineKeyboardMarkup:
    """Get image size selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Малый (600x400)", callback_data="size_600_400"),
            InlineKeyboardButton(text="💻 Средний (800x600)", callback_data="size_800_600")
        ],
        [
            InlineKeyboardButton(text="🖥️ Большой (1024x768)", callback_data="size_1024_768"),
            InlineKeyboardButton(text="📺 Очень большой (1200x900)", callback_data="size_1200_900")
        ],
        [
            InlineKeyboardButton(text="🔙 Настройки", callback_data="settings")
        ]
    ])


def get_font_settings_keyboard() -> InlineKeyboardMarkup:
    """Get font settings keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔤 Шрифт", callback_data="font_family"),
            InlineKeyboardButton(text="📏 Размер", callback_data="font_size")
        ],
        [
            InlineKeyboardButton(text="🎨 Цвет текста", callback_data="text_color"),
            InlineKeyboardButton(text="🖼️ Цвет фона", callback_data="bg_color")
        ],
        [
            InlineKeyboardButton(text="🔙 Настройки", callback_data="settings")
        ]
    ])


def get_font_family_keyboard() -> InlineKeyboardMarkup:
    """Get font family selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Arial", callback_data="font_Arial"),
            InlineKeyboardButton(text="Times New Roman", callback_data="font_Times")
        ],
        [
            InlineKeyboardButton(text="Helvetica", callback_data="font_Helvetica"),
            InlineKeyboardButton(text="Courier New", callback_data="font_Courier")
        ],
        [
            InlineKeyboardButton(text="🔙 Стили шрифта", callback_data="font_settings")
        ]
    ])


def get_font_size_keyboard() -> InlineKeyboardMarkup:
    """Get font size selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔤 Мелкий (12px)", callback_data="fontsize_12"),
            InlineKeyboardButton(text="📝 Средний (14px)", callback_data="fontsize_14")
        ],
        [
            InlineKeyboardButton(text="📖 Большой (16px)", callback_data="fontsize_16"),
            InlineKeyboardButton(text="📰 Очень большой (18px)", callback_data="fontsize_18")
        ],
        [
            InlineKeyboardButton(text="🔙 Стили шрифта", callback_data="font_settings")
        ]
    ])


def get_log_level_keyboard() -> InlineKeyboardMarkup:
    """Get log level selection keyboard.""" 
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔇 ERROR", callback_data="loglevel_ERROR"),
            InlineKeyboardButton(text="⚠️ WARNING", callback_data="loglevel_WARNING")
        ],
        [
            InlineKeyboardButton(text="ℹ️ INFO", callback_data="loglevel_INFO"), 
            InlineKeyboardButton(text="🔍 DEBUG", callback_data="loglevel_DEBUG")
        ],
        [
            InlineKeyboardButton(text="🔙 Настройки", callback_data="settings")
        ]
    ]) 