"""Admin command handlers for Telegram user client."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Callable, Awaitable

from pyrogram import Client
from pyrogram.types import Message as PyrogramMessage
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db_manager
from services.mirror import MirrorService

logger = logging.getLogger(__name__)


class AdminCommandHandler:
    """Handler for admin commands in Telegram user client."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = get_db_manager()
    
    async def handle_help_command(self, client: Client, message: PyrogramMessage) -> None:
        """Send help message with available commands."""
        help_text = """
🤖 **Telegram Mirror Bot - Admin Commands**

Available commands:
• `/help` - Show this help message
• `/status` - Show bot status and statistics
• `/mirrors` - List all mirror configurations
• `/add_mirror <source_id> <target_id> [topic_id]` - Add new mirror
• `/remove_mirror <mirror_id>` - Remove mirror configuration
• `/chats` - List all available chats

**Examples:**
`/add_mirror -1001234567890 -1009876543210`
`/add_mirror -1001234567890 -1009876543210 123`
`/remove_mirror 1`

For more information, check the documentation.
        """
        
        await client.send_message(
            chat_id=message.chat.id,
            text=help_text,
            reply_to_message_id=message.id,
        )
    
    async def handle_status_command(self, client: Client, message: PyrogramMessage) -> None:
        """Send bot status message."""
        try:
            async with self.db_manager.get_session() as session:
                mirror_service = MirrorService(session)
                
                # Get statistics
                mirrors = await mirror_service.get_active_mirrors()
                
                status_text = f"""
📊 **Bot Status**

🔄 **Active Mirrors:** {len(mirrors)}
🏃‍♂️ **Status:** Running
🗄️ **Database:** Connected
📱 **Session:** Active

⚙️ **Configuration:**
• Render Images: {self.settings.mirror.render_images}
• Max Image Width: {self.settings.mirror.max_image_width}px
• Max Image Height: {self.settings.mirror.max_image_height}px

Last updated: {asyncio.get_event_loop().time()}
                """
                
                await client.send_message(
                    chat_id=message.chat.id,
                    text=status_text,
                    reply_to_message_id=message.id,
                )
                
        except Exception as e:
            logger.exception("Error generating status message")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Error retrieving status information.",
                reply_to_message_id=message.id,
            )
    
    async def handle_mirrors_command(self, client: Client, message: PyrogramMessage) -> None:
        """Send list of mirror configurations."""
        try:
            async with self.db_manager.get_session() as session:
                mirror_service = MirrorService(session)
                mirrors = await mirror_service.get_active_mirrors()
                
                if not mirrors:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="📝 No active mirrors configured.",
                        reply_to_message_id=message.id,
                    )
                    return
                
                mirrors_text = "📋 **Active Mirrors:**\n\n"
                for mirror in mirrors:
                    source_title = mirror.source_chat.title or f"Chat {mirror.source_chat_id}"
                    target_title = mirror.target_chat.title or f"Chat {mirror.target_chat_id}"
                    
                    mirrors_text += f"""
**Mirror #{mirror.id}**
📤 From: {source_title} (`{mirror.source_chat_id}`)
📥 To: {target_title} (`{mirror.target_chat_id}`)
{f"🎯 Topic: {mirror.target_topic_id}" if mirror.target_topic_id else ""}
🖼️ Render as Image: {"✅" if mirror.render_as_image else "❌"}
📎 Include Media: {"✅" if mirror.include_media else "❌"}
💬 Include Replies: {"✅" if mirror.include_replies else "❌"}
                    """
                
                await client.send_message(
                    chat_id=message.chat.id,
                    text=mirrors_text,
                    reply_to_message_id=message.id,
                )
                
        except Exception as e:
            logger.exception("Error generating mirrors list")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Error retrieving mirrors information.",
                reply_to_message_id=message.id,
            )
    
    async def handle_add_mirror_command(
        self, 
        client: Client, 
        message: PyrogramMessage
    ) -> None:
        """Handle add mirror command."""
        try:
            if len(message.command) < 3:
                help_text = """
❌ **Неверный формат команды**

**Использование:** `/add_mirror <source_chat_id> <target_chat_id> [topic_id]`

**Форматы ID чатов:**
• **Группы/Супергруппы:** `-1001234567890` (начинаются с `-100`)
• **Обычные группы:** `-1234567890` (начинаются с `-`)
• **Каналы:** `-1001234567890` (начинаются с `-100`)
• **Личные чаты:** `1234567890` (положительные числа)

**Важно:** 
🤖 **Юзербот должен быть участником обоих чатов** (источника и назначения)
📋 Используйте `/chats` для просмотра доступных чатов

**Примеры:**
`/add_mirror -1001234567890 -1009876543210`
`/add_mirror 1234567890 -1001111111111`
`/add_mirror -1001234567890 -1009876543210 123`
                """
                await client.send_message(
                    chat_id=message.chat.id,
                    text=help_text,
                    reply_to_message_id=message.id,
                )
                return
            
            source_chat_id = int(message.command[1])
            target_chat_id = int(message.command[2])
            target_topic_id = int(message.command[3]) if len(message.command) > 3 else None
            
            # Validate chat access
            try:
                source_chat = await client.get_chat(source_chat_id)
                source_chat_name = source_chat.title or source_chat.first_name or f"Chat {source_chat_id}"
            except Exception as e:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ Не удается получить доступ к исходному чату `{source_chat_id}`\n"
                         f"Убедитесь, что юзербот является участником этого чата.",
                    reply_to_message_id=message.id,
                )
                return
            
            try:
                target_chat = await client.get_chat(target_chat_id)
                target_chat_name = target_chat.title or target_chat.first_name or f"Chat {target_chat_id}"
            except Exception as e:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ Не удается получить доступ к целевому чату `{target_chat_id}`\n"
                         f"Убедитесь, что юзербот является участником этого чата.",
                    reply_to_message_id=message.id,
                )
                return
            
            async with self.db_manager.get_session() as session:
                mirror_service = MirrorService(session)
                
                mirror = await mirror_service.create_mirror_configuration(
                    source_chat_id=source_chat_id,
                    target_chat_id=target_chat_id,
                    target_topic_id=target_topic_id,
                )
                
                if mirror:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"✅ **Зеркало #{mirror.id} создано успешно!**\n\n"
                             f"📤 **Источник:** {source_chat_name} (`{source_chat_id}`)\n"
                             f"📥 **Назначение:** {target_chat_name} (`{target_chat_id}`)"
                             f"{f'\n🎯 **Топик:** {target_topic_id}' if target_topic_id else ''}\n\n"
                             f"🔄 Зеркалирование активно!",
                        reply_to_message_id=message.id,
                    )
                else:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="❌ Не удалось создать конфигурацию зеркала.",
                        reply_to_message_id=message.id,
                    )
                    
        except ValueError as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ **Неверный формат ID чата**\n\n"
                     f"Ошибка: {str(e)}\n\n"
                     f"**Правильные форматы:**\n"
                     f"• Группы/каналы: `-1001234567890`\n"
                     f"• Личные чаты: `1234567890`\n"
                     f"• Используйте `/chats` для просмотра доступных чатов",
                reply_to_message_id=message.id,
            )
        except Exception as e:
            logger.exception("Error handling add mirror command")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Error creating mirror configuration.",
                reply_to_message_id=message.id,
            )
    
    async def handle_remove_mirror_command(
        self, 
        client: Client, 
        message: PyrogramMessage
    ) -> None:
        """Handle remove mirror command."""
        try:
            if len(message.command) < 2:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="❌ Usage: `/remove_mirror <mirror_id>`",
                    reply_to_message_id=message.id,
                )
                return
            
            mirror_id = int(message.command[1])
            
            async with self.db_manager.get_session() as session:
                mirror_service = MirrorService(session)
                
                success = await mirror_service.delete_mirror(mirror_id)
                
                if success:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"✅ Mirror #{mirror_id} removed successfully!",
                        reply_to_message_id=message.id,
                    )
                else:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"❌ Mirror #{mirror_id} not found or could not be removed.",
                        reply_to_message_id=message.id,
                    )
                    
        except ValueError:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Invalid mirror ID format. Use numeric ID.",
                reply_to_message_id=message.id,
            )
        except Exception as e:
            logger.exception("Error handling remove mirror command")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Error removing mirror configuration.",
                reply_to_message_id=message.id,
            )
    
    async def handle_chats_command(
        self, 
        client: Client, 
        message: PyrogramMessage
    ) -> None:
        """Handle chats command to list all available chats."""
        try:
            chats_data = []
            chat_count = 0
            
            # Get all dialogs (chats) from the client
            async for dialog in client.get_dialogs():
                chat = dialog.chat
                chat_type = chat.type.value if chat.type else "unknown"
                
                # Format chat info
                if chat.title:
                    chat_name = chat.title
                elif chat.first_name:
                    chat_name = f"{chat.first_name}"
                    if chat.last_name:
                        chat_name += f" {chat.last_name}"
                elif chat.username:
                    chat_name = f"@{chat.username}"
                else:
                    chat_name = "Unknown"
                
                # Add emoji based on chat type
                emoji = "👤" if chat_type == "private" else "🏢" if chat_type == "group" else "📢"
                
                chats_data.append({
                    "name": chat_name,
                    "id": chat.id,
                    "type": chat_type,
                    "username": chat.username,
                    "emoji": emoji
                })
                
                chat_count += 1
                
                # Limit to prevent too much data
                if chat_count >= 100:
                    break
            
            # Split into chunks
            chunk_size = 20  # 20 chats per message
            chunks = [chats_data[i:i + chunk_size] for i in range(0, len(chats_data), chunk_size)]
            
            if len(chunks) > 5:  # If more than 5 chunks, send to saved messages
                # Create full text
                full_text = "📋 **Полный список чатов:**\n\n"
                for chat_data in chats_data:
                    full_text += f"{chat_data['emoji']} **{chat_data['name']}**\n"
                    full_text += f"   ID: `{chat_data['id']}`\n"
                    full_text += f"   Type: {chat_data['type']}\n"
                    if chat_data['username']:
                        full_text += f"   Username: @{chat_data['username']}\n"
                    full_text += "\n"
                
                # Split into parts for saved messages
                parts = []
                current_part = ""
                for line in full_text.split('\n'):
                    if len(current_part + line + '\n') > 4000:
                        if current_part:
                            parts.append(current_part)
                        current_part = line + '\n'
                    else:
                        current_part += line + '\n'
                
                if current_part:
                    parts.append(current_part)
                
                # Send to saved messages
                for i, part in enumerate(parts):
                    header = f"📋 **Список чатов (часть {i+1}/{len(parts)})**\n\n" if len(parts) > 1 else ""
                    await client.send_message(
                        chat_id="me",
                        text=header + part
                    )
                
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"📋 Список из {chat_count} чатов отправлен в избранное (слишком большой список)",
                    reply_to_message_id=message.id,
                )
            else:
                # Send first chunk directly
                if chunks:
                    chats_text = f"📋 **Доступные чаты (показано {len(chats_data)} из {chat_count}):**\n\n"
                    for chat_data in chunks[0]:
                        chats_text += f"{chat_data['emoji']} **{chat_data['name']}**\n"
                        chats_text += f"   ID: `{chat_data['id']}`\n"
                        chats_text += f"   Type: {chat_data['type']}\n"
                        if chat_data['username']:
                            chats_text += f"   Username: @{chat_data['username']}\n"
                        chats_text += "\n"
                    
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=chats_text,
                        reply_to_message_id=message.id,
                    )
                    
                    # If there are more chunks, inform about saved messages
                    if len(chunks) > 1:
                        for i, chunk in enumerate(chunks[1:], 2):
                            chunk_text = f"📋 **Чаты (часть {i}):**\n\n"
                            for chat_data in chunk:
                                chunk_text += f"{chat_data['emoji']} **{chat_data['name']}**\n"
                                chunk_text += f"   ID: `{chat_data['id']}`\n"
                                chunk_text += f"   Type: {chat_data['type']}\n"
                                if chat_data['username']:
                                    chunk_text += f"   Username: @{chat_data['username']}\n"
                                chunk_text += "\n"
                            
                            await client.send_message(
                                chat_id="me",
                                text=chunk_text
                            )
                        
                        await client.send_message(
                            chat_id=message.chat.id,
                            text=f"📋 Остальные {len(chats_data) - chunk_size} чатов отправлены в избранное",
                            reply_to_message_id=message.id,
                        )
                else:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="📋 Чатов не найдено",
                        reply_to_message_id=message.id,
                    )
                
        except Exception as e:
            logger.exception("Error handling chats command")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Ошибка при получении списка чатов",
                reply_to_message_id=message.id,
            )

    async def handle_copy_message_command(
        self,
        client: Client,
        message: PyrogramMessage,
    ) -> None:
        """Download media from a message and re-upload it to a target chat.

        Usage: /copy_message <source_chat_id> <message_id> [message_id ...] <target_chat_id>
        """
        try:
            parts = message.command or []
            if len(parts) < 4:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=(
                        "❌ Неверный формат команды\n\n"
                        "Использование: `/copy_message <source_chat_id> <message_id> [message_id ...] <target_chat_id>`\n\n"
                        "Пример: `/copy_message -1002651305316 40 94 248 1266978055`"
                    ),
                    reply_to_message_id=message.id,
                )
                return

            source_chat_id = int(parts[1])
            target_chat_id = int(parts[-1])
            raw_ids = parts[2:-1]
            if not raw_ids:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="❌ Укажите хотя бы один ID сообщения между исходным и целевым чатами.",
                    reply_to_message_id=message.id,
                )
                return

            message_ids: list[int] = []
            bad_tokens: list[str] = []
            for tok in raw_ids:
                try:
                    message_ids.append(int(tok))
                except Exception:
                    bad_tokens.append(tok)

            if bad_tokens:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"⚠️ Пропущены некорректные ID: {' '.join(bad_tokens)}",
                    reply_to_message_id=message.id,
                )

            # Create single status message to edit throughout the process
            status = await client.send_message(
                chat_id=message.chat.id,
                text="⏳ Подготовка к копированию...",
                reply_to_message_id=message.id,
            )

            async def status_update(text: str) -> None:
                try:
                    await client.edit_message_text(
                        chat_id=status.chat.id,
                        message_id=status.id,
                        text=text,
                    )
                except Exception:
                    # Message might be deleted or same content; ignore and continue
                    pass

            total = len(message_ids)
            ok = 0
            fail = 0
            done = 0
            sem = asyncio.Semaphore(6)

            async def worker(idx: int, mid: int) -> None:
                nonlocal ok, fail, done
                async with sem:
                    await status_update(f"▶️ [{idx}/{total}] Обработка сообщения {mid}...")
                    try:
                        success = await self._save_one_message(
                            client=client,
                            source_chat_id=source_chat_id,
                            source_message_id=mid,
                            target_chat_id=target_chat_id,
                            status_update=status_update,
                        )
                        if success:
                            ok += 1
                        else:
                            fail += 1
                    except Exception:
                        logger.exception("Batch item failed in copy_message")
                        fail += 1
                    finally:
                        done += 1
                        await status_update(f"⏱️ Прогресс: {done}/{total} | ✅ {ok} | ❌ {fail}")

            tasks = [asyncio.create_task(worker(i, mid)) for i, mid in enumerate(message_ids, start=1)]
            await asyncio.gather(*tasks)
            await status_update(f"📊 Готово. Успешно: {ok} | Ошибок: {fail} | Всего: {total}")
        except Exception:
            logger.exception("Error processing /copy_message")
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Error processing /copy_message.",
                reply_to_message_id=message.id,
            )

    async def _save_one_message(
        self,
        client: Client,
        source_chat_id: int,
        source_message_id: int,
        target_chat_id: int,
        status_update: Callable[[str], Awaitable[None]],
    ) -> bool:
        """Process a single message copy (download + re-upload). Returns True if sent."""
        try:
            logger.info(
                f"/copy_message requested: from_chat={source_chat_id} message_id={source_message_id} to_chat={target_chat_id}"
            )

            await status_update("⏳ Обрабатываю: проверяю доступ и получаю сообщение...")

            # Verify access to target chat early
            try:
                _ = await client.get_chat(target_chat_id)
            except Exception:
                await status_update(
                    f"❌ Не удается получить доступ к целевому чату `{target_chat_id}`\n"
                    f"Убедитесь, что юзербот является участником этого чата."
                )
                return False

            # Fetch source message
            try:
                src_msg = await client.get_messages(source_chat_id, source_message_id)
                logger.info("Source message fetched successfully")
            except Exception:
                await status_update(
                    f"❌ Не удалось получить сообщение `{source_message_id}` из чата `{source_chat_id}`.\n"
                    f"Проверьте ID и доступ юзербота к чату."
                )
                logger.exception("Failed to fetch source message")
                return False

            # Determine media type
            media_type = ""
            if src_msg.photo:
                media_type = "photo"
            elif src_msg.video:
                media_type = "video"
            elif src_msg.document:
                media_type = "document"
            elif src_msg.audio:
                media_type = "audio"
            elif src_msg.voice:
                media_type = "voice"
            elif src_msg.animation:
                media_type = "animation"

            caption_text = src_msg.caption if src_msg.caption else None
            caption_entities = src_msg.caption_entities if src_msg.caption_entities else None

            # If no media – try sending text
            if not media_type:
                if src_msg.text:
                    logger.info("No media found, sending text")
                    await client.send_message(
                        chat_id=target_chat_id,
                        text=src_msg.text,
                        entities=(src_msg.entities if src_msg.entities else None),
                    )
                    await status_update(
                        f"✅ Текстовое сообщение `{source_message_id}` отправлено в `{target_chat_id}`"
                    )
                    return True
                await status_update(
                    f"❌ В сообщении `{source_message_id}` нет поддерживаемого медиа или текста."
                )
                return False

            # Prepare download target in user's Downloads to avoid double downloads
            downloads_dir = Path.home() / "Downloads" / "TelegramMirror"
            try:
                downloads_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                logger.exception("Failed to create downloads directory; will fallback to temp")
                downloads_dir = Path(tempfile.mkdtemp(prefix="tg_save_"))

            # We'll keep the downloaded media file; thumbnail will be temporary
            temp_dir = tempfile.mkdtemp(prefix="tg_save_thumb_")
            download_path = None
            thumb_path = None
            try:
                await status_update("⬇️ Скачиваю медиа...")

                # Pre-compute desired filename (may be refined below after metadata)
                desired_filename: str | None = None
                media_type = "video" if src_msg.video else "photo" if src_msg.photo else "document" if src_msg.document else "audio" if src_msg.audio else "voice" if src_msg.voice else "animation" if src_msg.animation else ""
                if media_type == "document" and src_msg.document and src_msg.document.file_name:
                    desired_filename = src_msg.document.file_name
                elif media_type == "audio" and src_msg.audio:
                    if src_msg.audio.file_name:
                        desired_filename = src_msg.audio.file_name
                    else:
                        performer = src_msg.audio.performer if src_msg.audio.performer else ""
                        title = src_msg.audio.title if src_msg.audio.title else ""
                        base = f"{performer.strip()} - {title.strip()}".strip(" -")
                        desired_filename = base or f"audio_{source_message_id}"
                elif media_type == "video" and src_msg.video:
                    desired_filename = src_msg.video.file_name if src_msg.video.file_name else f"video_{source_message_id}"
                elif media_type == "voice":
                    desired_filename = f"voice_{source_message_id}"
                elif media_type == "animation" and src_msg.animation:
                    desired_filename = src_msg.animation.file_name if src_msg.animation.file_name else f"animation_{source_message_id}"

                if desired_filename:
                    desired_filename = desired_filename.replace("/", "_").replace("\\", "_")
                else:
                    desired_filename = f"media_{source_message_id}"

                # Ensure extension later after actual download if missing
                target_file_path = downloads_dir / desired_filename

                # Perform download directly into Downloads (file path)
                download_path = await client.download_media(
                    src_msg,
                    file_name=str(target_file_path),
                )
                logger.info(f"Media downloaded to {download_path}")

                # Ensure extension: if user-provided name lacked ext, inherit from actual path
                try:
                    actual_ext = os.path.splitext(download_path)[1]
                    target_ext = os.path.splitext(str(target_file_path))[1]
                    if not target_ext and actual_ext:
                        fixed = str(target_file_path) + actual_ext
                        os.replace(download_path, fixed)
                        download_path = fixed
                except Exception:
                    logger.exception("Failed to ensure file extension for downloaded media")

                # Try to fetch thumbnail for better preview where supported
                try:
                    if media_type == "video" and src_msg.video:
                        if src_msg.video.thumbs:
                            t = src_msg.video.thumbs[-1]
                            thumb_path = await client.download_media(t, file_name=os.path.join(temp_dir, "thumb.jpg"))
                    elif media_type == "audio" and src_msg.audio and src_msg.audio.thumbs:
                        t = src_msg.audio.thumbs[-1]
                        thumb_path = await client.download_media(t, file_name=os.path.join(temp_dir, "thumb.jpg"))
                    elif media_type == "document" and src_msg.document and src_msg.document.thumbs:
                        t = src_msg.document.thumbs[-1]
                        thumb_path = await client.download_media(t, file_name=os.path.join(temp_dir, "thumb.jpg"))
                except Exception:
                    logger.exception("Failed to download thumbnail; will proceed without it")
            except Exception:
                logger.exception("Failed to download media for copy_message")
                await status_update(
                    f"❌ Не удалось скачать медиа из сообщения `{source_message_id}`.\n"
                    f"Чат может ограничивать сохранение контента."
                )
                # Cleanup directory if created without file
                try:
                    if os.path.isdir(temp_dir):
                        for entry in os.listdir(temp_dir):
                            os.remove(os.path.join(temp_dir, entry))
                        os.rmdir(temp_dir)
                except Exception:
                    logger.exception("Failed to cleanup temp directory after download error")
                return False

            # Re-upload based on media type
            try:
                await status_update("⬆️ Отправляю медиа в целевой чат...")
                try:
                    match media_type:
                        case "photo":
                            await client.send_photo(
                                chat_id=target_chat_id,
                                photo=download_path,
                                caption=caption_text,
                                caption_entities=caption_entities,
                            )
                        case "video":
                            # pass duration/size and thumb if available
                            duration = src_msg.video.duration if src_msg.video and src_msg.video.duration else None
                            width = src_msg.video.width if src_msg.video and src_msg.video.width else None
                            height = src_msg.video.height if src_msg.video and src_msg.video.height else None
                            kwargs = {}
                            if duration is not None:
                                kwargs["duration"] = duration
                            if width is not None:
                                kwargs["width"] = width
                            if height is not None:
                                kwargs["height"] = height
                            if thumb_path:
                                kwargs["thumb"] = thumb_path
                            kwargs["supports_streaming"] = True
                            await client.send_video(
                                chat_id=target_chat_id,
                                video=download_path,
                                caption=caption_text,
                                caption_entities=caption_entities,
                                **kwargs,
                            )
                        case "document":
                            kwargs = {"caption": caption_text, "caption_entities": caption_entities}
                            if thumb_path:
                                kwargs["thumb"] = thumb_path
                            await client.send_document(
                                chat_id=target_chat_id,
                                document=download_path,
                                **kwargs,
                            )
                        case "audio":
                            duration = src_msg.audio.duration if src_msg.audio and src_msg.audio.duration else None
                            performer = src_msg.audio.performer if src_msg.audio and src_msg.audio.performer else None
                            title = src_msg.audio.title if src_msg.audio and src_msg.audio.title else None
                            kwargs = {"caption": caption_text, "caption_entities": caption_entities}
                            if duration is not None:
                                kwargs["duration"] = duration
                            if performer:
                                kwargs["performer"] = performer
                            if title:
                                kwargs["title"] = title
                            if thumb_path:
                                kwargs["thumb"] = thumb_path
                            await client.send_audio(
                                chat_id=target_chat_id,
                                audio=download_path,
                                **kwargs,
                            )
                        case "voice":
                            duration = src_msg.voice.duration if src_msg.voice and src_msg.voice.duration else None
                            kwargs = {"caption": caption_text, "caption_entities": caption_entities}
                            if duration is not None:
                                kwargs["duration"] = duration
                            await client.send_voice(
                                chat_id=target_chat_id,
                                voice=download_path,
                                **kwargs,
                            )
                        case "animation":
                            await client.send_animation(
                                chat_id=target_chat_id,
                                animation=download_path,
                                caption=caption_text,
                                caption_entities=caption_entities,
                            )
                        case _:
                            await client.send_document(
                                chat_id=target_chat_id,
                                document=download_path,
                                caption=caption_text,
                                caption_entities=caption_entities,
                            )
                except Exception:
                    logger.exception("Typed send failed, retrying without thumb if present")
                    try:
                        if media_type == "video":
                            duration = src_msg.video.duration if src_msg.video and src_msg.video.duration else None
                            width = src_msg.video.width if src_msg.video and src_msg.video.width else None
                            height = src_msg.video.height if src_msg.video and src_msg.video.height else None
                            kwargs = {"caption": caption_text, "caption_entities": caption_entities, "supports_streaming": True}
                            if duration is not None:
                                kwargs["duration"] = duration
                            if width is not None:
                                kwargs["width"] = width
                            if height is not None:
                                kwargs["height"] = height
                            await client.send_video(chat_id=target_chat_id, video=download_path, **kwargs)
                        elif media_type == "audio":
                            duration = src_msg.audio.duration if src_msg.audio and src_msg.audio.duration else None
                            performer = src_msg.audio.performer if src_msg.audio and src_msg.audio.performer else None
                            title = src_msg.audio.title if src_msg.audio and src_msg.audio.title else None
                            kwargs = {"caption": caption_text, "caption_entities": caption_entities}
                            if duration is not None:
                                kwargs["duration"] = duration
                            if performer:
                                kwargs["performer"] = performer
                            if title:
                                kwargs["title"] = title
                            await client.send_audio(chat_id=target_chat_id, audio=download_path, **kwargs)
                        elif media_type == "voice":
                            duration = src_msg.voice.duration if src_msg.voice and src_msg.voice.duration else None
                            kwargs = {"caption": caption_text, "caption_entities": caption_entities}
                            if duration is not None:
                                kwargs["duration"] = duration
                            await client.send_voice(chat_id=target_chat_id, voice=download_path, **kwargs)
                        else:
                            await client.send_document(chat_id=target_chat_id, document=download_path, caption=caption_text, caption_entities=caption_entities)
                    except Exception:
                        logger.exception("Retried typed send failed, falling back to document")
                        await client.send_document(
                            chat_id=target_chat_id,
                            document=download_path,
                            caption=caption_text,
                            caption_entities=caption_entities,
                        )

                await status_update(
                    f"✅ Готово: медиа из `{source_message_id}` отправлено в `{target_chat_id}`"
                )
                logger.info("Media re-uploaded successfully")
                return True
            except Exception:
                logger.exception("Failed to re-upload media for copy_message")
                await status_update(f"❌ Ошибка при отправке медиа в `{target_chat_id}`.")
                return False
            finally:
                try:
                    # keep the media file in Downloads; remove only thumbnail and its temp dir
                    if thumb_path and os.path.isfile(thumb_path):
                        os.remove(thumb_path)
                    if os.path.isdir(temp_dir):
                        for entry in os.listdir(temp_dir):
                            try:
                                os.remove(os.path.join(temp_dir, entry))
                            except Exception:
                                logger.exception("Failed to remove temp thumb file during cleanup")
                        os.rmdir(temp_dir)
                except Exception:
                    logger.exception("Cleanup failed after copy_message")
        except Exception:
            logger.exception("Unexpected error in _save_one_message")
            return False