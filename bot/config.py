"""Bot設定管理モジュール

既存の環境変数のみを使用し、その他は適切なデフォルト値を持つ。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Bot設定クラス

    環境変数から設定を読み込み、型チェックとバリデーションを実行します。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # === 既存の環境変数 ===
    discord_token: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # === ハードコード定数（環境変数不要） ===
    @property
    def api_timeout(self) -> float:
        """APIタイムアウト（秒）"""
        return 30.0

    @property
    def api_base_url(self) -> str:
        """APIベースURLを構築"""
        # ポートが80または443の場合はポート番号を省略
        if self.api_port in (80, 443):
            return f"http://{self.api_host}"
        return f"http://{self.api_host}:{self.api_port}"

    @property
    def persona_select_timeout(self) -> int:
        """ペルソナ選択UIのタイムアウト（秒）"""
        return 180

    @property
    def description_max_length(self) -> int:
        """説明文の最大文字数"""
        return 100

    @property
    def conversation_history_limit(self) -> int:
        """保存する会話履歴の最大件数"""
        return 20

    @property
    def conversation_context_window(self) -> int:
        """LLMに送信する会話履歴の件数"""
        return 10


# グローバル設定インスタンス
_settings: BotSettings | None = None


def get_settings() -> BotSettings:
    """設定インスタンスを取得（シングルトン）"""
    global _settings
    if _settings is None:
        _settings = BotSettings()
    return _settings


def reload_settings() -> BotSettings:
    """設定を再読み込み（主にテスト用）"""
    global _settings
    _settings = BotSettings()
    return _settings
