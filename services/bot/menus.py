"""Menu texts and content for Telegram bot."""

from config import get_settings


def get_main_menu_text() -> str:
    """Get main menu text."""
    return """
🤖 <b>Telegram Mirror Bot - Панель управления</b>

Добро пожаловать в административную панель бота!

Используйте кнопки ниже для управления:
• ⚙️ Настройки - основные параметры бота
• 🔄 Зеркала - управление зеркалированием
• 💬 Чаты - список чатов и их настройки  
• 👥 Пользователи - управление правами доступа
• 📊 Статистика - статистика работы бота

Для быстрого доступа используйте команды:
/settings, /mirrors, /chats, /users, /stats
    """


def get_settings_menu_text() -> str:
    """Get settings menu text."""
    settings = get_settings()
    
    return f"""
⚙️ <b>Настройки бота</b>

<b>Текущие настройки:</b>

🖼️ <b>Рендеринг сообщений:</b> {'✅ Включен' if settings.mirror.render_images else '❌ Отключен'}
📐 <b>Размер изображений:</b> {settings.mirror.max_image_width}x{settings.mirror.max_image_height}
🎨 <b>Шрифт:</b> {settings.render.font_family}, {settings.render.font_size}px
📝 <b>Уровень логирования:</b> {settings.logging.level}

Выберите параметр для изменения:
    """


def get_mirrors_menu_text(mirrors_count: int) -> str:
    """Get mirrors menu text."""
    return f"""
🔄 <b>Управление зеркалами</b>

📊 <b>Активных зеркал:</b> {mirrors_count}

Выберите зеркало для просмотра/редактирования или добавьте новое.

<i>Зеркало - это связь между чатом-источником и чатом-назначением.
Сообщения из источника автоматически копируются в назначение.</i>
    """


def get_chats_menu_text(source_count: int, target_count: int) -> str:
    """Get chats menu text."""
    return f"""
💬 <b>Управление чатами</b>

📤 <b>Чатов-источников:</b> {source_count}
📥 <b>Чатов-назначений:</b> {target_count}

<b>Чаты-источники</b> - откуда берутся сообщения для зеркалирования
<b>Чаты-назначения</b> - куда отправляются зеркалированные сообщения

<i>Для получения ID чата отправьте любое сообщение в нужном чате.
ID появится в логах бота.</i>
    """


def get_users_menu_text(admins_count: int, allowed_count: int) -> str:
    """Get users menu text.""" 
    return f"""
👥 <b>Управление пользователями</b>

👑 <b>Администраторов:</b> {admins_count}
✅ <b>Разрешенных пользователей:</b> {allowed_count}

<b>Администраторы</b> могут управлять ботом через команды
<b>Разрешенные пользователи</b> - чьи сообщения будут зеркалироваться

<i>Только сообщения от разрешенных пользователей попадают в зеркала.</i>
    """


def get_stats_menu_text(mirrors_count: int, chats_count: int, users_count: int) -> str:
    """Get statistics menu text."""
    settings = get_settings()
    
    return f"""
📊 <b>Статистика бота</b>

🔄 <b>Активных зеркал:</b> {mirrors_count}
💬 <b>Отслеживаемых чатов:</b> {chats_count}
👥 <b>Разрешенных пользователей:</b> {users_count}

🖼️ <b>Рендеринг изображений:</b> {'✅ Включен' if settings.mirror.render_images else '❌ Отключен'}
🗄️ <b>База данных:</b> {settings.database.url.split('://')[0].upper()}
🌍 <b>Окружение:</b> {settings.environment.title()}

<i>Обновляется в реальном времени</i>
    """


def get_help_menu_text() -> str:
    """Get help menu text."""
    return """
❓ <b>Помощь</b>

<b>🔧 Основные команды:</b>
/start - главное меню
/settings - настройки бота
/mirrors - управление зеркалами
/chats - управление чатами
/users - управление пользователями
/stats - статистика

<b>📋 Как получить ID чата:</b>
1. Отправьте любое сообщение в нужном чате
2. Посмотрите логи бота - там появится ID
3. Или используйте @userinfobot для получения ID

<b>👤 Как получить ID пользователя:</b>
1. Пользователь должен написать боту любое сообщение
2. Его ID появится в логах бота
3. Или найдите @userinfobot в Telegram

<b>⚙️ Настройка зеркалирования:</b>
1. Добавьте чаты-источники (откуда брать сообщения)
2. Добавьте чаты-назначения (куда отправлять)
3. Создайте зеркало между ними
4. Настройте права доступа пользователей
5. Проверьте работу, отправив тестовое сообщение

<b>🔐 Безопасность:</b>
• Только администраторы могут управлять ботом
• Токены хранятся в зашифрованном виде
• Доступ к настройкам ограничен

<b>⚡ Производительность:</b>
• Рендеринг изображений можно отключить
• База данных SQLite подходит для малых нагрузок
• Для больших объемов используйте PostgreSQL
    """


def get_mirror_details_text(mirror) -> str:
    """Get mirror details text."""
    source_title = (mirror.source_chat.title if mirror.source_chat and mirror.source_chat.title else None) or f"Chat {mirror.source_chat_id}"
    target_title = (mirror.target_chat.title if mirror.target_chat and mirror.target_chat.title else None) or f"Chat {mirror.target_chat_id}"
    
    return f"""
🔄 <b>Детали зеркала #{mirror.id}</b>

📤 <b>Источник:</b> {source_title}
   <code>{mirror.source_chat_id}</code>

📥 <b>Назначение:</b> {target_title}
   <code>{mirror.target_chat_id}</code>

🔄 <b>Статус:</b> {'✅ Активно' if mirror.is_active else '❌ Неактивно'}
📅 <b>Создано:</b> {mirror.created_at.strftime('%d.%m.%Y %H:%M')}
📊 <b>Обработано сообщений:</b> {len(mirror.messages) if ('messages' in mirror.__dict__ and mirror.messages is not None) else 0}

<i>Для изменения настроек используйте кнопки ниже</i>
    """


def get_chat_details_text(chat) -> str:
    """Get chat details text."""
    title = (chat.title if chat and chat.title else None) or f"Chat {chat.chat_id}"
    
    return f"""
💬 <b>Детали чата</b>

📝 <b>Название:</b> {title}
🆔 <b>ID:</b> <code>{chat.chat_id}</code>
👤 <b>Тип:</b> {chat.type if chat and chat.type else 'Неизвестно'}
📅 <b>Добавлен:</b> {chat.created_at.strftime('%d.%m.%Y %H:%M')}

<i>Скопируйте ID для настройки зеркал</i>
    """


def get_user_details_text(user) -> str:
    """Get user details text."""
    name = (user.first_name if user and user.first_name else None) or f"User {user.user_id}"
    username = user.username if user and user.username else None
    
    return f"""
👤 <b>Детали пользователя</b>

📝 <b>Имя:</b> {name}
🆔 <b>ID:</b> <code>{user.user_id}</code>
👤 <b>Username:</b> {'@' + username if username else 'Не указан'}
👑 <b>Администратор:</b> {'✅ Да' if (user.is_admin if user and (user.is_admin is not None) else False) else '❌ Нет'}
✅ <b>Разрешен:</b> {'✅ Да' if (user.is_allowed if user and (user.is_allowed is not None) else True) else '❌ Нет'}
📅 <b>Добавлен:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}

<i>Изменить права можно кнопками ниже</i>
    """


def get_add_mirror_text() -> str:
    """Get add mirror instruction text."""
    return """
➕ <b>Добавление нового зеркала</b>

⚠️ <b>ВАЖНО:</b> Зеркала создаются через <b>юзербот</b>, а не этот бот!

Отправьте команду <b>юзерботу</b> в личные сообщения:

<code>/add_mirror &lt;source_id&gt; &lt;target_id&gt; [topic_id]</code>

<b>🆔 Форматы ID чатов:</b>
• <b>Группы/Супергруппы:</b> <code>-1001234567890</code> (начинаются с -100)
• <b>Обычные группы:</b> <code>-1234567890</code> (начинаются с -)
• <b>Каналы:</b> <code>-1001234567890</code> (начинаются с -100)
• <b>Личные чаты:</b> <code>1234567890</code> (положительные числа)

<b>📝 Примеры команд:</b>
<code>/add_mirror -1001234567890 -1009876543210</code>
<code>/add_mirror 1234567890 -1001111111111</code>
<code>/add_mirror -1001234567890 -1009876543210 123</code>

<b>🔍 Для просмотра чатов:</b>
Отправьте <code>/chats</code> юзерботу

<b>⚡ Требования:</b>
🤖 Юзербот должен быть участником обоих чатов
✅ У юзербота должны быть права на отправку сообщений
    """


def get_add_chat_text() -> str:
    """Get add chat instruction text."""
    return """
➕ <b>Добавление чата</b>

<b>📋 Как получить ID чата:</b>
1. Добавьте бота в нужный чат
2. Отправьте любое сообщение в чате
3. ID чата появится в логах бота

<b>📝 Отправьте ID чата:</b>
ID должен выглядеть как <code>-100123456789</code>

<i>После добавления чат можно будет использовать в зеркалах</i>
    """


def get_add_user_text() -> str:
    """Get add user instruction text."""
    return """
➕ <b>Добавление пользователя</b>

<b>📋 Как получить ID пользователя:</b>
1. Пользователь должен написать боту любое сообщение
2. Его ID появится в логах бота
3. Или найдите @userinfobot в Telegram

<b>📝 Отправьте ID пользователя:</b>
ID должен выглядеть как <code>123456789</code>

<b>⚙️ Укажите права через пробел:</b>
• <code>admin</code> - администратор
• <code>allowed</code> - разрешенный пользователь

<b>Примеры:</b>
<code>123456789 admin</code> - добавить администратора
<code>987654321 allowed</code> - добавить разрешенного пользователя

<i>Администраторы могут управлять ботом</i>
    """ 