"""Discord Bot イベントハンドラーモジュール

このモジュールは、Discord Botのビジネスロジックを管理します。
PersonaBotクラスからロジックを分離し、SOLID原則に準拠した設計を実現します。

Modules:
    command_handler: スラッシュコマンドのビジネスロジック
    message_handler: メッセージイベントのビジネスロジック
"""

from bot.handlers.command_handler import CommandHandler
from bot.handlers.message_handler import MessageHandler

__all__ = ["CommandHandler", "MessageHandler"]
