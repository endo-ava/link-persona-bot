"""API カスタム例外定義

アプリケーション全体で使用するカスタム例外階層を定義します。
適切な例外処理とエラーメッセージの一貫性を確保します。
"""

from typing import Any


class LinkPersonaBotError(Exception):
    """基底例外クラス

    全てのカスタム例外の基底となるクラス。
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ArticleFetchError(LinkPersonaBotError):
    """記事取得エラー

    URLから記事を取得できない場合に発生します。
    """
    pass


class ArticleParseError(LinkPersonaBotError):
    """記事解析エラー

    取得した記事を解析できない場合に発生します。
    """
    pass


class LLMError(LinkPersonaBotError):
    """LLMエラー

    LLM APIの呼び出しに失敗した場合に発生します。
    """
    pass


class LLMTimeoutError(LLMError):
    """LLMタイムアウトエラー

    LLM APIのレスポンスがタイムアウトした場合に発生します。
    """
    pass


class LLMRateLimitError(LLMError):
    """LLMレート制限エラー

    LLM APIのレート制限に達した場合に発生します。
    """
    pass


class PersonaNotFoundError(LinkPersonaBotError):
    """ペルソナ未検出エラー

    指定されたペルソナが見つからない場合に発生します。
    """
    pass


class InvalidRequestError(LinkPersonaBotError):
    """不正なリクエストエラー

    リクエストパラメータが不正な場合に発生します。
    """
    pass


class ConfigurationError(LinkPersonaBotError):
    """設定エラー

    アプリケーション設定が不正な場合に発生します。
    """
    pass
