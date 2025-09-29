# 📱 Telegram Mirror Bot

Современный Telegram бот для зеркалирования сообщений между чатами с возможностью рендеринга сообщений в виде изображений.

## ✨ Основные возможности

- 🔄 **Зеркалирование сообщений** между Telegram чатами
- 🖼️ **Рендеринг сообщений в изображения** для красивого отображения
- 🗄️ **SQLAlchemy ORM** для надежного хранения данных
- ⚙️ **Pydantic настройки** с валидацией конфигурации
- 🔧 **Модульная архитектура** без циркулярных импортов
- 📝 **Детальное логирование** всех операций
- 🛡️ **Система прав доступа** (админы и разрешенные пользователи)
- 💬 **Админ команды** для управления через Telegram

## 🏗️ Архитектура проекта

```
telegram_mirror/
├── config/                    # Конфигурация приложения
│   ├── __init__.py
│   └── settings.py           # Pydantic настройки
├── database/                 # Работа с базой данных
│   ├── __init__.py
│   ├── engine.py            # SQLAlchemy движок
│   ├── models.py            # Модели данных
│   └── repositories.py      # Репозитории для операций с БД
├── services/                 # Бизнес-логика
│   ├── __init__.py
│   ├── mirror_service.py    # Основная логика зеркалирования
│   ├── message_renderer.py  # Рендеринг сообщений в изображения
│   └── telegram_service.py  # Управление Telegram клиентом
├── sessions/                 # Сессии Telegram (создается автоматически)
├── rendered_messages/        # Рендеренные изображения (создается автоматически)
├── main.py                   # Точка входа в приложение
├── requirements.txt          # Зависимости Python
├── .env.example             # Пример конфигурации
└── README.md                # Документация
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Клонируем репозиторий
git clone <repository-url>
cd telegram_mirror

# Создаем виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows

# Устанавливаем зависимости
pip install -r requirements.txt

# Рекомендуется: установить TgCrypto для ускорения работы
pip install TgCrypto
```

### 2. Настройка конфигурации

```bash
# Копируем пример конфигурации
cp .env.example .env

# Редактируем .env файл с вашими данными
nano .env
```

### 3. Инициализация базы данных

```bash
# Применяем миграции базы данных
alembic upgrade head
```

**Обязательные параметры для настройки:**

1. **Telegram API**: Получите на https://my.telegram.org/auth
   ```env
   TELEGRAM__API_ID=12345678
   TELEGRAM__API_HASH=your_api_hash_here
   ```

2. **ID чатов и пользователей**:
   ```env
   MIRROR__SOURCE_CHAT_IDS=-1001234567890,-1009876543210
   MIRROR__TARGET_CHAT_IDS=-1001111111111,-1002222222222
   MIRROR__ADMIN_USER_IDS=1266978055,7561878018
   MIRROR__ALLOWED_USER_IDS=1266978055,6889183661,2351485193
   ```

### 4. Запуск бота

```bash
python main.py
```

При первом запуске потребуется авторизация через код из Telegram.

## 📋 Админ команды

Доступны администраторам в личных сообщениях:

- `/help` - Справка по командам
- `/status` - Статус бота и статистика
- `/mirrors` - Список всех зеркал
- `/add_mirror <source_id> <target_id> [topic_id]` - Добавить зеркало
- `/remove_mirror <mirror_id>` - Удалить зеркало

**Примеры:**
```
/add_mirror -1001234567890 -1009876543210
/add_mirror -1001234567890 -1009876543210 123
/remove_mirror 1
```

## 🔧 Конфигурация

### Настройки рендеринга

```env
# Включить рендеринг сообщений как изображения
MIRROR__RENDER_IMAGES=true

# Максимальные размеры изображений
MIRROR__MAX_IMAGE_WIDTH=800
MIRROR__MAX_IMAGE_HEIGHT=1200

# Стили рендеринга
RENDER__FONT_FAMILY=Arial
RENDER__FONT_SIZE=14
RENDER__BACKGROUND_COLOR=#FFFFFF
RENDER__TEXT_COLOR=#000000
RENDER__PADDING=20
RENDER__BORDER_RADIUS=10
```

### База данных

**SQLite (по умолчанию):**
```env
DATABASE__URL=sqlite+aiosqlite:///./telegram_mirror.db
```

**PostgreSQL (рекомендуется для продакшена):**
```env
DATABASE__URL=postgresql+asyncpg://user:password@localhost:5432/telegram_mirror
```

### Логирование

```env
LOGGING__LEVEL=INFO
LOGGING__FILE_PATH=logs/telegram_mirror.log
```

## 🔍 Как получить ID чатов и пользователей

### 📋 Форматы ID в Telegram:

**Группы и каналы:**
- **Супергруппы/каналы**: `-1001234567890` (начинаются с `-100`)
- **Обычные группы**: `-1234567890` (начинаются с `-`)
- **Личные чаты**: `1234567890` (положительные числа)

### 🔍 Способы получения ID:

**ID чатов (простой способ):**
1. Отправьте команду `/chats` юзерботу в личные сообщения
2. Получите полный список всех доступных чатов с их ID

**ID чатов (альтернативный способ):**
1. Добавьте юзербота в чат
2. Отправьте любое сообщение 
3. Посмотрите в логи - там появится ID чата

**ID пользователей:**
1. Отправьте `/start` боту @userinfobot
2. Получите ваш ID
3. Или попросите пользователя написать любое сообщение юзерботу - ID появится в логах

### ⚠️ Важные особенности:

- **Pyrogram** и **Aiogram** используют одинаковые форматы ID
- ID **не меняются** со временем
- **Супергруппы** создаются из обычных групп при превышении 200 участников
- При превращении группы в супергруппу **ID меняется** с `-123` на `-100123`

## 🛠️ Разработка

### Структура кода

- **config/** - Настройки с валидацией через Pydantic
- **database/** - Модели и репозитории SQLAlchemy
- **services/** - Бизнес-логика без привязки к фреймворкам
- **main.py** - Точка входа с graceful shutdown

### Принципы:

1. **Без циркулярных импортов** - четкая иерархия модулей
2. **Repository pattern** - абстракция работы с БД
3. **Service layer** - бизнес-логика отделена от инфраструктуры
4. **Dependency injection** - через контекст-менеджеры
5. **Type hints** - полная типизация кода

### Запуск в режиме разработки:

```bash
# Включить debug режим
echo "DEBUG=true" >> .env
echo "ENVIRONMENT=development" >> .env

# Включить подробное логирование SQLAlchemy
echo "DATABASE__ECHO=true" >> .env

python main.py
```

## 📊 Мониторинг

### Логи
```bash
# Просмотр логов в реальном времени
tail -f logs/telegram_mirror.log

# Поиск ошибок
grep "ERROR" logs/telegram_mirror.log
```

### База данных
```bash
# SQLite
sqlite3 telegram_mirror.db "SELECT COUNT(*) FROM messages;"

# PostgreSQL
psql -d telegram_mirror -c "SELECT COUNT(*) FROM messages;"
```

## 🔒 Безопасность

1. **Не коммитьте .env файлы** в git
2. **Используйте PostgreSQL** в продакшене
3. **Ограничьте список разрешенных пользователей**
4. **Регулярно обновляйте зависимости**
5. **Мониторьте логи** на предмет подозрительной активности

## 🐛 Устранение неполадок

### Частые проблемы:

**1. Ошибка авторизации Telegram:**
```bash
# Удалите сессию и авторизуйтесь заново
rm sessions/*.session*
```

**2. Ошибки базы данных:**
```bash
# Проверьте права доступа к файлу БД
ls -la telegram_mirror.db

# Пересоздайте БД (ОСТОРОЖНО - удалит все данные!)
rm telegram_mirror.db
```

**3. Проблемы с рендерингом:**
```bash
# Проверьте установку зависимостей для html2image
pip install --upgrade html2image pillow
```

### Логи отладки:
```env
LOGGING__LEVEL=DEBUG
```

## 📝 Changelog

### v2.0.0 (Текущая версия)
- ✅ Полная переработка архитектуры
- ✅ SQLAlchemy вместо JSON конфигурации  
- ✅ Pydantic настройки с валидацией
- ✅ Рендеринг сообщений в изображения
- ✅ Repository pattern
- ✅ Исправлены циркулярные импорты
- ✅ Админ команды через Telegram
- ✅ Graceful shutdown
- ✅ Детальное логирование

### v1.0.0 (Старая версия)
- ❌ Циркулярные импорты
- ❌ JSON конфигурация
- ❌ Простое копирование сообщений

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 📞 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте [Issues](../../issues) на GitHub
2. Создайте новый Issue с подробным описанием
3. Приложите логи и конфигурацию (без секретных данных!)

---

**⚡ Telegram Mirror Bot - Зеркалируйте сообщения красиво!** 