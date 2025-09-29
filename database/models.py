"""SQLAlchemy models for Telegram Mirror Bot."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class TimestampMixin:
    """Mixin for created/updated timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base, TimestampMixin):
    """Telegram user model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class Chat(Base, TimestampMixin):
    """Telegram chat model."""
    
    __tablename__ = "chats"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50))  # private, group, supergroup, channel
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_source: Mapped[bool] = mapped_column(Boolean, default=False)
    is_target: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )
    source_mirrors: Mapped[list["Mirror"]] = relationship(
        "Mirror", 
        foreign_keys="Mirror.source_chat_id",
        back_populates="source_chat",
        cascade="all, delete-orphan"
    )
    target_mirrors: Mapped[list["Mirror"]] = relationship(
        "Mirror",
        foreign_keys="Mirror.target_chat_id", 
        back_populates="target_chat",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title={self.title}, type={self.type})>"


class Message(Base, TimestampMixin):
    """Telegram message model."""
    
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    reply_to_message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    message_thread_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    
    text: Mapped[Optional[str]] = mapped_column(Text)
    media_type: Mapped[Optional[str]] = mapped_column(String(50))  # photo, video, document, etc.
    media_file_id: Mapped[Optional[str]] = mapped_column(String(255))
    media_file_unique_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    is_forwarded: Mapped[bool] = mapped_column(Boolean, default=False)
    forward_from_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    forward_from_user_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    forward_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    is_mirrored: Mapped[bool] = mapped_column(Boolean, default=False)
    mirror_count: Mapped[int] = mapped_column(Integer, default=0)
    rendered_image_path: Mapped[Optional[str]] = mapped_column(String(512))
    
    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, telegram_id={self.telegram_id}, chat_id={self.chat_id})>"


class Mirror(Base, TimestampMixin):
    """Mirror configuration model."""
    
    __tablename__ = "mirrors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id"), nullable=False, index=True
    )
    target_chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chats.id"), nullable=False, index=True
    )
    target_topic_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    render_as_image: Mapped[bool] = mapped_column(Boolean, default=True)
    include_media: Mapped[bool] = mapped_column(Boolean, default=True)
    include_replies: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    source_chat: Mapped["Chat"] = relationship(
        "Chat", 
        foreign_keys=[source_chat_id],
        back_populates="source_mirrors"
    )
    target_chat: Mapped["Chat"] = relationship(
        "Chat",
        foreign_keys=[target_chat_id], 
        back_populates="target_mirrors"
    )
    
    def __repr__(self) -> str:
        return f"<Mirror(id={self.id}, source={self.source_chat_id}, target={self.target_chat_id})>" 