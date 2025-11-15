"""APIレスポンスの型定義

TypedDictを使用してAPIレスポンスの型安全性を確保します。
"""

from typing import TypedDict


class PersonaInfo(TypedDict):
    """ペルソナ情報"""
    name: str
    icon: str
    color: int
    description: str


class IngestResponse(TypedDict):
    """記事要約レスポンス"""
    summary: str
    persona: PersonaInfo
    article_title: str
    article_url: str


class DebateResponse(TypedDict):
    """ディベートレスポンス"""
    response: str
    persona: PersonaInfo
    context_used: int  # 使用した会話履歴の数


class HealthResponse(TypedDict):
    """ヘルスチェックレスポンス"""
    status: str
    version: str


class ErrorResponse(TypedDict):
    """エラーレスポンス"""
    detail: str
    error_type: str
