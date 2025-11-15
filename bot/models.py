"""Bot用型定義

TypedDictを使用してBot内部およびAPI通信の型安全性を確保します。
"""

from __future__ import annotations

from typing import TypedDict, NotRequired


class PersonaInfo(TypedDict):
    """ペルソナ情報"""
    name: str
    icon: str
    color: int
    description: str


class IngestRequest(TypedDict):
    """記事要約リクエスト"""
    url: str
    persona_id: NotRequired[str | None]
    user_id: NotRequired[str | None]
    guild_id: NotRequired[str | None]


class IngestResponse(TypedDict):
    """記事要約レスポンス"""
    summary: str
    persona: PersonaInfo
    article_title: str
    article_url: str


class DebateRequest(TypedDict):
    """ディベートリクエスト"""
    persona_id: str
    user_message: str
    conversation_history: list[ConversationMessage]


class DebateResponse(TypedDict):
    """ディベートレスポンス"""
    response: str
    persona: PersonaInfo
    context_used: int


class ConversationMessage(TypedDict):
    """会話メッセージ"""
    role: str  # "user" or "assistant"
    content: str


class ChannelState(TypedDict):
    """チャンネル状態"""
    persona_id: str
    history: list[ConversationMessage]
