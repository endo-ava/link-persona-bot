"""API クライアント

FastAPI バックエンドと通信するための HTTP クライアント。
DRY原則に基づき、共通リクエストメソッドを実装しています。
"""

import logging
from typing import Any, Optional

import httpx

from bot.config import get_settings
from bot.models import (
    ConversationMessage,
    IngestRequest,
    IngestResponse,
    DebateRequest,
    DebateResponse,
)

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """API クライアントエラーの基底クラス"""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class APIClient:
    """FastAPI バックエンドと通信するクライアント

    全てのHTTPリクエストを共通メソッドで処理し、
    エラーハンドリングとログを統一します。
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        """クライアントを初期化

        Args:
            base_url: APIのベースURL（省略時は設定から取得）
            timeout: リクエストタイムアウト秒数（省略時は設定から取得）
        """
        settings = get_settings()
        self.base_url = base_url or settings.api_base_url
        self.timeout = timeout or settings.api_timeout

        logger.info(
            "API client initialized",
            extra={"base_url": self.base_url, "timeout": self.timeout}
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """共通HTTPリクエストメソッド

        Args:
            method: HTTPメソッド（GET, POST等）
            endpoint: エンドポイントパス
            json_data: JSONボディ
            params: クエリパラメータ

        Returns:
            レスポンスのJSONデータ

        Raises:
            APIClientError: リクエスト失敗時
        """
        url = f"{self.base_url}{endpoint}"

        logger.debug(
            f"Making {method} request",
            extra={
                "url": url,
                "has_json_data": json_data is not None,
                "has_params": params is not None
            }
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                )

                # ステータスコードをログ
                logger.info(
                    f"{method} request completed",
                    extra={
                        "url": url,
                        "status_code": response.status_code
                    }
                )

                # エラーレスポンスの処理
                if response.status_code >= 400:
                    error_detail = "Unknown error"
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("detail", str(error_json))
                    except Exception:
                        error_detail = response.text or f"HTTP {response.status_code}"

                    logger.error(
                        f"API request failed with status {response.status_code}",
                        extra={
                            "url": url,
                            "status_code": response.status_code,
                            "error_detail": error_detail
                        }
                    )

                    raise APIClientError(
                        message=f"API request failed: {error_detail}",
                        status_code=response.status_code,
                        details={"url": url, "error": error_detail}
                    )

                # 成功レスポンスのパース
                try:
                    return response.json()
                except Exception as e:
                    logger.error(
                        "Failed to parse JSON response",
                        extra={"url": url, "error": str(e)},
                        exc_info=True
                    )
                    raise APIClientError(
                        message=f"Failed to parse response JSON: {str(e)}",
                        details={"url": url, "error": str(e)}
                    ) from e

        except httpx.TimeoutException as e:
            logger.error(
                "Request timeout",
                extra={"url": url, "timeout": self.timeout},
                exc_info=True
            )
            raise APIClientError(
                message=f"Request timeout after {self.timeout}s",
                details={"url": url, "timeout": self.timeout}
            ) from e

        except httpx.RequestError as e:
            logger.error(
                "Request error",
                extra={"url": url, "error": str(e)},
                exc_info=True
            )
            raise APIClientError(
                message=f"Request failed: {str(e)}",
                details={"url": url, "error": str(e)}
            ) from e

        except APIClientError:
            # 既にAPIClientErrorの場合は再スロー
            raise

        except Exception as e:
            logger.error(
                "Unexpected error during request",
                extra={"url": url, "error": str(e)},
                exc_info=True
            )
            raise APIClientError(
                message=f"Unexpected error: {str(e)}",
                details={"url": url, "error": str(e)}
            ) from e

    async def ingest_url(
        self,
        url: str,
        persona_id: Optional[str] = None,
        user_id: Optional[str] = None,
        guild_id: Optional[str] = None,
    ) -> IngestResponse:
        """URL を要約する

        Args:
            url: 要約する記事のURL
            persona_id: 使用するペルソナID（省略時は自動選択）
            user_id: ユーザーID（オプション）
            guild_id: ギルドID（オプション）

        Returns:
            要約レスポンス

        Raises:
            APIClientError: リクエスト失敗時
        """
        logger.info(
            "Ingesting URL",
            extra={
                "url": url,
                "persona_id": persona_id,
                "user_id": user_id,
                "guild_id": guild_id
            }
        )

        request_data: IngestRequest = {
            "url": url,
            "persona_id": persona_id,
            "user_id": user_id,
            "guild_id": guild_id,
        }
        response_data = await self._make_request(
            method="POST",
            endpoint="/ingest",
            json_data=request_data,
        )

        # TypedDictとして返す（型チェックのため）
        return IngestResponse(**response_data)

    async def debate(
        self,
        persona_id: str,
        user_message: str,
        conversation_history: list[ConversationMessage],
    ) -> DebateResponse:
        """ペルソナとディベートする

        Args:
            persona_id: ペルソナID
            user_message: ユーザーメッセージ
            conversation_history: 会話履歴（ConversationMessageのリスト）

        Returns:
            ディベートレスポンス

        Raises:
            APIClientError: リクエスト失敗時
        """
        logger.info(
            "Starting debate",
            extra={
                "persona_id": persona_id,
                "conversation_history_count": len(conversation_history)
            }
        )

        request_data: DebateRequest = {
            "persona_id": persona_id,
            "user_message": user_message,
            "conversation_history": conversation_history,
        }

        response_data = await self._make_request(
            method="POST",
            endpoint="/debate",
            json_data=request_data,
        )

        # TypedDictとして返す
        return DebateResponse(**response_data)


# シングルトンインスタンス
_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """API クライアントのシングルトンインスタンスを取得

    Returns:
        APIクライアント
    """
    global _client
    if _client is None:
        _client = APIClient()
    return _client


def reset_api_client() -> None:
    """API クライアントをリセット（主にテスト用）"""
    global _client
    _client = None
