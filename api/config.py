"""API設定管理モジュール

既存の環境変数のみを使用し、その他は適切なデフォルト値を持つ。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API設定クラス

    環境変数から設定を読み込み、型チェックとバリデーションを実行します。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # === 既存の環境変数（LLM関連） ===
    llm_provider: str = "qwen"
    llm_api_key: str
    llm_api_url: str = ""
    llm_model: str = "qwen-plus"
    llm_extra_header_http_referer: str = ""
    llm_extra_header_x_title: str = ""

    # === 既存の環境変数（API関連） ===
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # === ハードコード定数（環境変数不要） ===
    @property
    def api_version(self) -> str:
        """APIバージョン"""
        return "1.0.0"

    @property
    def api_timeout(self) -> float:
        """APIタイムアウト（秒）"""
        return 30.0

    @property
    def cors_origins(self) -> list[str]:
        """CORS許可オリジン"""
        return ["*"]

    @property
    def article_max_length(self) -> int:
        """記事の最大文字数"""
        return 2000

    @property
    def summary_min_length(self) -> int:
        """要約の最小文字数"""
        return 100

    @property
    def summary_max_length(self) -> int:
        """要約の最大文字数"""
        return 150


# グローバル設定インスタンス
_settings: APISettings | None = None


def get_settings() -> APISettings:
    """設定インスタンスを取得（シングルトン）"""
    global _settings
    if _settings is None:
        _settings = APISettings()
    return _settings


def reload_settings() -> APISettings:
    """設定を再読み込み（主にテスト用）"""
    global _settings
    _settings = APISettings()
    return _settings
