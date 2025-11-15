"""記事要約サービス

記事の取得、ペルソナ選択、要約生成のビジネスロジックを担当します。
"""

import logging
from typing import Optional

from api.config import get_settings
from api.exceptions import (
    ArticleFetchError,
    ArticleParseError,
    LLMError,
    PersonaNotFoundError,
)
from api.fetcher import ArticleFetcher
from api.llm_client import LLMClient
from api.models.responses import IngestResponse, PersonaInfo
from api.persona_loader import PersonaLoader, Persona

logger = logging.getLogger(__name__)


class ArticleService:
    """記事要約サービスクラス

    URLから記事を取得し、適切なペルソナで要約を生成します。
    """

    def __init__(
        self,
        article_fetcher: ArticleFetcher,
        llm_client: LLMClient,
        persona_loader: PersonaLoader,
    ) -> None:
        """初期化

        Args:
            article_fetcher: 記事取得クライアント
            llm_client: LLMクライアント
            persona_loader: ペルソナローダー
        """
        self.article_fetcher = article_fetcher
        self.llm_client = llm_client
        self.persona_loader = persona_loader
        self.settings = get_settings()

    async def generate_summary(
        self,
        url: str,
        persona_id: Optional[str] = None,
        user_id: Optional[str] = None,
        guild_id: Optional[str] = None,
    ) -> IngestResponse:
        """記事を要約する

        Args:
            url: 記事URL
            persona_id: ペルソナID（Noneの場合は自動選択）
            user_id: ユーザーID（将来的なパーソナライズ用）
            guild_id: ギルドID（将来的な統計用）

        Returns:
            要約レスポンス

        Raises:
            ArticleFetchError: 記事取得失敗
            PersonaNotFoundError: ペルソナ未検出
            LLMError: LLM呼び出し失敗
        """
        logger.info(
            "Starting article summary generation",
            extra={
                "url": url,
                "persona_id": persona_id,
                "user_id": user_id,
                "guild_id": guild_id,
            }
        )

        try:
            # 1. 記事を取得
            article = await self.article_fetcher.fetch_article(url)
            logger.info(
                "Article fetched successfully",
                extra={
                    "url": url,
                    "title": article.get("title"),
                    "content_length": len(article["content"]),
                    "truncated": article["truncated"],
                }
            )

            # 2. ペルソナを選択または取得
            persona = self._select_persona(persona_id)
            logger.info(
                "Persona selected",
                extra={"persona_id": persona.id, "persona_name": persona.name}
            )

            # 3. 要約を生成
            summary = await self._generate_persona_summary(article, persona)
            logger.info(
                "Summary generated successfully",
                extra={"summary_length": len(summary)}
            )

            # 4. レスポンスを構築
            return IngestResponse(
                summary=summary,
                persona=PersonaInfo(
                    name=persona.name,
                    icon=persona.icon,
                    color=persona.color,
                    description=persona.description,
                ),
                article_title=article.get("title", "（タイトルなし）"),
                article_url=article["url"],
            )

        except ArticleFetchError:
            logger.error("Failed to fetch article", extra={"url": url}, exc_info=True)
            raise
        except PersonaNotFoundError:
            logger.error(
                "Persona not found", extra={"persona_id": persona_id}, exc_info=True
            )
            raise
        except LLMError:
            logger.error("LLM generation failed", extra={"url": url}, exc_info=True)
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during summary generation",
                extra={"url": url, "error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to generate summary",
                details={"url": url, "error": str(e)}
            ) from e

    def _select_persona(self, persona_id: Optional[str]) -> Persona:
        """ペルソナを選択する

        Args:
            persona_id: ペルソナID（Noneの場合は自動選択）

        Returns:
            選択されたペルソナ

        Raises:
            PersonaNotFoundError: ペルソナが見つからない
        """
        if persona_id:
            # 指定されたペルソナを使用
            persona = self.persona_loader.get_persona(persona_id)
            if not persona:
                raise PersonaNotFoundError(
                    f"Persona '{persona_id}' not found",
                    details={"persona_id": persona_id}
                )
            return persona
        else:
            # デフォルトペルソナを使用
            # TODO: 記事の内容に応じた自動選択ロジックを実装
            all_personas = self.persona_loader.get_all_personas()
            if not all_personas:
                raise PersonaNotFoundError(
                    "No personas available",
                    details={}
                )
            return next(iter(all_personas.values()))

    async def _generate_persona_summary(
        self,
        article: dict,
        persona: Persona,
    ) -> str:
        """ペルソナの人格で記事を要約する

        Args:
            article: 記事データ
            persona: ペルソナ

        Returns:
            要約文

        Raises:
            LLMError: LLM呼び出し失敗
        """
        # 要約生成プロンプト
        user_prompt = f"""以下の記事を、あなたの人格で{self.settings.summary_min_length}〜{self.settings.summary_max_length}字で要約してください。

記事タイトル: {article.get('title', '(タイトルなし)')}

記事本文:
{article['content'][:self.settings.article_max_length]}

要約を生成してください:"""

        try:
            summary = await self.llm_client.generate_persona_response(
                system_prompt=persona.get_system_message(),
                user_message=user_prompt,
            )
            return summary.strip()
        except Exception as e:
            logger.error(
                "Failed to generate summary with LLM",
                extra={"persona_id": persona.id, "error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to generate summary with LLM",
                details={"persona_id": persona.id, "error": str(e)}
            ) from e
