"""Discord Bot カスタム例外定義

API側のexceptions.pyと同様のパターンを採用。
ドメイン固有のエラーハンドリングを可能にする。
"""

from typing import Any


class BotError(Exception):
    """Discord Bot基底例外クラス

    全てのBot固有例外の親クラス。
    エラーメッセージと詳細情報を保持。
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Args:
            message: エラーメッセージ
            details: エラーの詳細情報（デバッグ用）
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CommandExecutionError(BotError):
    """スラッシュコマンド実行時のエラー

    /persona, /debate などのコマンド処理で発生したエラー。
    ユーザーに対してエラーメッセージを表示する際に使用。
    """
    pass


class MessageHandlingError(BotError):
    """メッセージ処理時のエラー

    on_messageイベントハンドラー内で発生したエラー。
    URL検出、メンション応答などの処理失敗時に使用。
    """
    pass


class URLDetectionError(BotError):
    """URL検出・処理時のエラー

    メッセージからのURL抽出や、URLコンテンツ取得時のエラー。
    """
    pass


class PersonaNotFoundError(BotError):
    """ペルソナが見つからない場合のエラー

    指定されたペルソナIDが存在しない、
    またはペルソナローダーで読み込めない場合に発生。
    """
    pass


class DiscordAPIError(BotError):
    """Discord API呼び出し時のエラー

    Discord APIとの通信失敗、レート制限超過など。
    discord.pyの例外をラップする際に使用。
    """
    pass


class ConversationHistoryError(BotError):
    """会話履歴管理のエラー

    ConversationManager でのデータ操作失敗時に発生。
    """
    pass
