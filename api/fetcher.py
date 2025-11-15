"""
記事抽出モジュール

URLから記事本文をクリーンなテキストとして抽出する。
trafilaturaを使用して静的HTMLサイトから本文を取得。
"""

from typing import Optional, Dict, Any
import httpx
import trafilatura
from trafilatura.settings import use_config


class ArticleFetchError(Exception):
    """記事取得時のエラー"""
    pass


class ArticleFetcher:
    """URLから記事を取得・抽出するクラス"""

    def __init__(
        self,
        timeout: float = 10.0,
        max_content_length: int = 2000,
    ) -> None:
        """
        Args:
            timeout: HTTPリクエストのタイムアウト（秒）
            max_content_length: 抽出する記事の最大文字数（コスト制御）
        """
        self.timeout = timeout
        self.max_content_length = max_content_length

        # trafilaturaの設定
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

    async def fetch_article(self, url: str) -> Dict[str, Any]:
        """
        URLから記事を取得し、本文を抽出する

        Args:
            url: 記事のURL

        Returns:
            記事情報を含む辞書:
            {
                "url": str,
                "title": str | None,
                "content": str,
                "truncated": bool,  # 切り詰められたかどうか
            }

        Raises:
            ArticleFetchError: 記事の取得または抽出に失敗した場合
        """
        # URLのバリデーション
        if not url.startswith(("http://", "https://")):
            raise ArticleFetchError(f"Invalid URL scheme: {url}")

        try:
            # HTMLを取得
            html_content = await self._fetch_html(url)

            # 本文を抽出
            extracted_data = self._extract_content(html_content)

            if not extracted_data or not extracted_data.get("content"):
                raise ArticleFetchError("Failed to extract article content")

            # コンテンツの長さを制限
            content = extracted_data["content"]
            truncated = len(content) > self.max_content_length

            if truncated:
                content = content[:self.max_content_length] + "..."

            return {
                "url": url,
                "title": extracted_data.get("title"),
                "content": content,
                "truncated": truncated,
            }

        except httpx.HTTPError as e:
            raise ArticleFetchError(f"Failed to fetch URL: {str(e)}") from e
        except Exception as e:
            raise ArticleFetchError(f"Unexpected error: {str(e)}") from e

    async def _fetch_html(self, url: str) -> str:
        """
        URLからHTMLコンテンツを取得

        Args:
            url: 取得先のURL

        Returns:
            HTMLコンテンツ

        Raises:
            httpx.HTTPError: HTTP通信エラー
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LinkPersonaBot/1.0; +https://github.com/endo-ava/link-persona-bot)"
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _extract_content(self, html: str) -> Optional[Dict[str, str]]:
        """
        HTMLから記事本文とタイトルを抽出

        Args:
            html: HTMLコンテンツ

        Returns:
            抽出結果:
            {
                "title": str | None,
                "content": str | None,
            }
        """
        # trafilaturaで本文抽出（メタデータも含む）
        content = trafilatura.extract(
            html,
            output_format="txt",
            include_comments=False,
            include_tables=False,
            config=self.config,
        )

        # タイトルも抽出を試みる
        metadata = trafilatura.extract_metadata(html)
        title = metadata.title if metadata else None

        if not content:
            return None

        return {
            "title": title,
            "content": content.strip(),
        }


# グローバルなArticleFetcherインスタンス
_article_fetcher: Optional[ArticleFetcher] = None


def get_article_fetcher() -> ArticleFetcher:
    """
    グローバルなArticleFetcherインスタンスを取得
    （シングルトンパターン）
    """
    global _article_fetcher
    if _article_fetcher is None:
        _article_fetcher = ArticleFetcher()
    return _article_fetcher
