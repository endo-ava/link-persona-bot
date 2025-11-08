"""
Link Persona Bot API クライアント

FastAPI バックエンドへのHTTPリクエストを行うクライアント
"""

import os
from typing import Optional, Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class APIClientError(Exception):
    """API呼び出し時のエラー"""
    pass


class LinkPersonaAPIClient:
    """Link Persona Bot APIとやり取りするクライアント"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Args:
            api_url: APIのベースURL（Noneの場合は環境変数 API_URLから取得、デフォルト: http://localhost:8000）
            timeout: HTTPリクエストのタイムアウト（秒）
        """
        self.api_url = api_url or os.getenv("API_URL", "http://localhost:8000")
        self.timeout = timeout

        # 末尾のスラッシュを削除
        self.api_url = self.api_url.rstrip("/")

    async def ingest_url(
        self,
        url: str,
        user_id: Optional[str] = None,
        guild_id: Optional[str] = None,
        persona_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        URLから記事を取得し、ペルソナベースで要約を生成

        Args:
            url: 記事のURL
            user_id: DiscordユーザーID（オプション）
            guild_id: DiscordサーバーID（オプション）
            persona_id: 使用するペルソナID（Noneの場合は自動選択）

        Returns:
            API応答:
            {
                "url": str,
                "title": str | None,
                "summary": str,
                "persona_id": str,
                "persona_name": str,
                "persona_icon": str,
                "persona_color": int,
                "truncated": bool,
            }

        Raises:
            APIClientError: API呼び出しに失敗した場合
        """
        endpoint = f"{self.api_url}/ingest"

        payload = {
            "url": url,
            "user_id": user_id,
            "guild_id": guild_id,
            "persona_id": persona_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            # HTTPエラーの場合、詳細を取得
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)

            raise APIClientError(
                f"Failed to ingest URL (HTTP {e.response.status_code}): {error_detail}"
            ) from e

        except httpx.ConnectError as e:
            raise APIClientError(
                f"Failed to connect to API server at {self.api_url}"
            ) from e

        except httpx.TimeoutException as e:
            raise APIClientError("API request timed out") from e

        except Exception as e:
            raise APIClientError(f"Unexpected error: {str(e)}") from e

    async def debate_article(
        self,
        url: str,
        original_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        記事の主張に対する反論を生成

        Args:
            url: 記事のURL
            original_summary: 元の要約（Noneの場合は記事から自動抽出）

        Returns:
            API応答:
            {
                "url": str,
                "original_stance": str,
                "counter_argument": str,
                "debate_summary": str,
            }

        Raises:
            APIClientError: API呼び出しに失敗した場合
        """
        endpoint = f"{self.api_url}/debate"

        payload = {
            "url": url,
            "original_summary": original_summary,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            # HTTPエラーの場合、詳細を取得
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)

            raise APIClientError(
                f"Failed to debate article (HTTP {e.response.status_code}): {error_detail}"
            ) from e

        except httpx.ConnectError as e:
            raise APIClientError(
                f"Failed to connect to API server at {self.api_url}"
            ) from e

        except httpx.TimeoutException as e:
            raise APIClientError("API request timed out") from e

        except Exception as e:
            raise APIClientError(f"Unexpected error: {str(e)}") from e


# グローバルなAPIクライアントインスタンス
_api_client: Optional[LinkPersonaAPIClient] = None


def get_api_client() -> LinkPersonaAPIClient:
    """
    グローバルなAPIクライアントインスタンスを取得
    （シングルトンパターン）
    """
    global _api_client
    if _api_client is None:
        _api_client = LinkPersonaAPIClient()
    return _api_client
