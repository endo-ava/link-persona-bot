"""
LLM (Large Language Model) API クライアント

OpenAI互換のAPIエンドポイントと通信する汎用クライアント。
Qwen, OpenAI, OpenRouter, その他OpenAI互換のLLMサービスに対応。
"""

import os
from typing import List, Dict, Optional, Any
from enum import Enum

import httpx
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


class LLMProvider(str, Enum):
    """サポートしているLLMプロバイダー"""
    OPENAI = "openai"
    QWEN = "qwen"
    OPENROUTER = "openrouter"
    AZURE = "azure"
    CUSTOM = "custom"


# プロバイダー別のデフォルト設定
PROVIDER_DEFAULTS: Dict[LLMProvider, Dict[str, str]] = {
    LLMProvider.OPENAI: {
        "api_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
    },
    LLMProvider.QWEN: {
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    LLMProvider.OPENROUTER: {
        "api_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-3.5-turbo",
    },
}


class LLMClient:
    """LLM API とのやり取りを行う汎用クライアント"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Args:
            api_key: LLM APIキー（Noneの場合は環境変数 LLM_API_KEY から取得）
            api_url: LLM APIのエンドポイントURL（Noneの場合は環境変数またはプロバイダー設定から取得）
            model: 使用するモデル名（Noneの場合は環境変数またはプロバイダー設定から取得）
            provider: LLMプロバイダー名（環境変数 LLM_PROVIDER から取得、デフォルト: qwen）
            extra_headers: 追加のHTTPヘッダー（OpenRouter等で必要）
        """
        # プロバイダーの決定
        self.provider: str = provider or os.getenv("LLM_PROVIDER", LLMProvider.QWEN)

        # プロバイダー別のデフォルト設定を取得
        provider_config: Dict[str, str] = PROVIDER_DEFAULTS.get(self.provider, {})

        # APIキーの取得
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LLM API key not found. Set LLM_API_KEY environment variable."
            )

        # API URLの決定（優先順位: 引数 > 環境変数 > プロバイダーデフォルト）
        self.api_url = (
            api_url
            or os.getenv("LLM_API_URL")
            or provider_config.get("api_url", "https://api.openai.com/v1")
        )

        # モデル名の決定（優先順位: 引数 > 環境変数 > プロバイダーデフォルト）
        self.model = (
            model
            or os.getenv("LLM_MODEL")
            or provider_config.get("model", "gpt-3.5-turbo")
        )

        # 追加ヘッダーの設定
        self.extra_headers = extra_headers or self._get_extra_headers_from_env()

    def _get_extra_headers_from_env(self) -> Dict[str, str]:
        """
        環境変数またはプロバイダー設定から追加ヘッダーを取得

        環境変数の例:
        - LLM_EXTRA_HEADER_HTTP_REFERER=https://example.com
        - LLM_EXTRA_HEADER_X_TITLE=My App
        """
        extra_headers = {}

        # OpenRouter用の追加ヘッダー
        if self.provider == LLMProvider.OPENROUTER:
            # HTTP-Refererは必須（OpenRouterのポリシー）
            referer = os.getenv("LLM_EXTRA_HEADER_HTTP_REFERER", "https://github.com")
            extra_headers["HTTP-Referer"] = referer

            # X-Titleはオプション（ランキング表示用）
            title = os.getenv("LLM_EXTRA_HEADER_X_TITLE", "Link Persona Bot")
            if title:
                extra_headers["X-Title"] = title

        # 環境変数から追加のカスタムヘッダーを読み込み
        # 形式: LLM_EXTRA_HEADER_<HEADER_NAME>=value
        for key, value in os.environ.items():
            if key.startswith("LLM_EXTRA_HEADER_") and key not in [
                "LLM_EXTRA_HEADER_HTTP_REFERER",
                "LLM_EXTRA_HEADER_X_TITLE",
            ]:
                header_name = key.replace("LLM_EXTRA_HEADER_", "").replace("_", "-")
                extra_headers[header_name] = value

        return extra_headers

    def _build_headers(self) -> Dict[str, str]:
        """APIリクエスト用のヘッダーを構築"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 追加ヘッダーをマージ
        if self.extra_headers:
            headers.update(self.extra_headers)

        return headers

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 500,
        top_p: float = 0.9,
        frequency_penalty: float = 0.3,
        presence_penalty: float = 0.2,
    ) -> str:
        """
        チャット補完APIを呼び出す

        Args:
            messages: メッセージのリスト [{"role": "user/assistant/system", "content": "..."}]
            temperature: 生成のランダム性 (0.0-2.0, デフォルト: 1.0)
            max_tokens: 最大生成トークン数
            top_p: nucleus sampling (0.0-1.0, デフォルト: 0.9)
            frequency_penalty: 同じ単語の繰り返しペナルティ (-2.0〜2.0, デフォルト: 0.3)
            presence_penalty: 新しいトピックへの誘導 (-2.0〜2.0, デフォルト: 0.2)

        Returns:
            生成されたテキスト

        Raises:
            RuntimeError: API呼び出しに失敗した場合、またはレスポンスが不正な場合
        """
        headers = self._build_headers()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data: Dict[str, Any] = response.json()

                # レスポンス構造のバリデーション
                if "choices" not in data or not data["choices"]:
                    raise ValueError("Invalid API response structure: no choices")

                if "message" not in data["choices"][0]:
                    raise ValueError("Invalid API response structure: no message in choice")

                if "content" not in data["choices"][0]["message"]:
                    raise ValueError("Invalid API response structure: no content in message")

                return data["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                # HTTPエラーの場合、安全なエラーメッセージを返す
                # （APIキーや機密情報が露出しないようにする）
                print(f"LLM API error: {e.response.status_code}")
                raise RuntimeError(
                    f"LLM service error: {e.response.status_code}"
                ) from e

            except (KeyError, IndexError, ValueError) as e:
                # レスポンス構造の検証エラー
                raise RuntimeError(
                    "Invalid response structure from LLM service"
                ) from e

            except httpx.ConnectError as e:
                # 接続エラー
                raise RuntimeError("Failed to connect to LLM service") from e

            except httpx.TimeoutException as e:
                # タイムアウトエラー
                raise RuntimeError("LLM service request timed out") from e

    async def generate_persona_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        ペルソナに基づいた応答を生成

        Args:
            system_prompt: ペルソナのシステムプロンプト
            user_message: ユーザーのメッセージ
            conversation_history: 会話履歴（オプション）

        Returns:
            ペルソナに基づいた応答テキスト
        """
        messages = [{"role": "system", "content": system_prompt}]

        # 会話履歴を追加（最新10件まで）
        if conversation_history:
            messages.extend(conversation_history[-10:])

        # 現在のユーザーメッセージを追加
        messages.append({"role": "user", "content": user_message})

        return await self.chat_completion(messages)


# グローバルなLLMクライアントインスタンス
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    グローバルなLLMクライアントインスタンスを取得
    （シングルトンパターン）
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
