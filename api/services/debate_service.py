"""ディベートサービス

記事の主張に対する反論生成とディベート形式のレスポンス生成を担当します。
"""

import logging
from typing import Optional

from api.config import get_settings
from api.exceptions import ArticleFetchError, LLMError
from api.fetcher import ArticleFetcher
from api.llm_client import LLMClient
from api.models.responses import DebateResponse, PersonaInfo
from api.persona_loader import PersonaLoader

logger = logging.getLogger(__name__)


class DebateService:
    """ディベートサービスクラス

    記事の主張を抽出し、反論を生成し、ディベート形式でまとめます。
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

    async def generate_debate(
        self,
        url: str,
        original_summary: Optional[str] = None,
        persona_id: Optional[str] = None,
        conversation_history: Optional[list[dict[str, str]]] = None,
    ) -> DebateResponse:
        """ディベートを生成する

        Args:
            url: 記事URL（将来的に使用予定）
            original_summary: 元の要約（省略可）
            persona_id: ペルソナID
            conversation_history: 会話履歴

        Returns:
            ディベートレスポンス

        Raises:
            ArticleFetchError: 記事取得失敗
            LLMError: LLM呼び出し失敗
        """
        logger.info(
            "Starting debate generation",
            extra={
                "url": url,
                "has_original_summary": original_summary is not None,
                "persona_id": persona_id,
                "conversation_history_count": len(conversation_history) if conversation_history else 0,
            }
        )

        try:
            # ペルソナを取得
            persona = self.persona_loader.get_persona(persona_id) if persona_id else None
            if not persona:
                # デフォルトペルソナを使用
                all_personas = self.persona_loader.get_all_personas()
                persona = next(iter(all_personas.values())) if all_personas else None

            # 会話履歴がある場合は、それを基にレスポンスを生成
            if conversation_history:
                response_text = await self._generate_conversation_response(
                    conversation_history=conversation_history,
                    persona=persona,
                )
            else:
                # 従来のディベートモード（記事ベース）
                response_text = await self._generate_article_debate(
                    url=url,
                    original_summary=original_summary,
                )

            logger.info(
                "Debate generated successfully",
                extra={"response_length": len(response_text)}
            )

            return DebateResponse(
                response=response_text,
                persona=PersonaInfo(
                    name=persona.name if persona else "アシスタント",
                    icon=persona.icon if persona else "💬",
                    color=persona.color if persona else 0x5865F2,
                    description=persona.description if persona else "親切なアシスタント",
                ),
                context_used=len(conversation_history) if conversation_history else 0,
            )

        except ArticleFetchError:
            logger.error("Failed to fetch article", extra={"url": url}, exc_info=True)
            raise
        except LLMError:
            logger.error("LLM generation failed", extra={"url": url}, exc_info=True)
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during debate generation",
                extra={"url": url, "error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to generate debate",
                details={"url": url, "error": str(e)}
            ) from e

    async def _generate_conversation_response(
        self,
        conversation_history: list[dict[str, str]],
        persona: Optional[object] = None,
    ) -> str:
        """会話履歴を基にレスポンスを生成

        Args:
            conversation_history: 会話履歴
            persona: ペルソナ

        Returns:
            レスポンステキスト
        """
        # システムプロンプトを設定
        system_prompt = (
            persona.get_system_message() if persona
            else "あなたは親切で役に立つアシスタントです。"
        )

        # 会話履歴を整形してLLMに送信
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)

        try:
            response = await self.llm_client.chat_completion(messages=messages)
            return response.strip()
        except Exception as e:
            logger.error(
                "Failed to generate conversation response",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to generate conversation response",
                details={"error": str(e)}
            ) from e

    async def _generate_article_debate(
        self,
        url: str,
        original_summary: Optional[str] = None,
    ) -> str:
        """記事ベースのディベートを生成

        Args:
            url: 記事URL
            original_summary: 元の要約

        Returns:
            ディベートテキスト
        """
        # 記事を取得
        article = await self.article_fetcher.fetch_article(url)
        logger.info(
            "Article fetched for debate",
            extra={
                "url": url,
                "title": article.get("title"),
                "content_length": len(article["content"]),
            }
        )

        # 元の主張を抽出
        if original_summary:
            original_stance = original_summary
        else:
            original_stance = await self._extract_stance(article)

        # 反論を生成
        counter_argument = await self._generate_counter_argument(original_stance)

        # ディベートのまとめを生成
        debate_summary = await self._generate_debate_summary(
            original_stance,
            counter_argument
        )

        # フォーマット
        return f"""【元の主張】
{original_stance.strip()}

【反論】
{counter_argument.strip()}

【まとめ】
{debate_summary.strip()}"""

    async def _extract_stance(self, article: dict) -> str:
        """記事から主張を抽出

        Args:
            article: 記事データ

        Returns:
            主張テキスト
        """
        stance_prompt = f"""以下の記事の主な主張やメッセージを{self.settings.summary_min_length}字程度で要約してください。

記事タイトル: {article.get('title', '(タイトルなし)')}
記事本文:
{article['content'][:self.settings.article_max_length]}

主張:"""

        try:
            stance = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "あなたは記事の主張を客観的に分析する専門家です。"},
                    {"role": "user", "content": stance_prompt}
                ]
            )
            return stance.strip()
        except Exception as e:
            logger.error(
                "Failed to extract stance",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to extract stance",
                details={"error": str(e)}
            ) from e

    async def _generate_counter_argument(self, original_stance: str) -> str:
        """反論を生成

        Args:
            original_stance: 元の主張

        Returns:
            反論テキスト
        """
        counter_prompt = f"""以下の主張に対して、反対の立場から説得力のある反論を{self.settings.summary_max_length}字程度で生成してください。

元の主張:
{original_stance}

反論:"""

        try:
            counter = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "あなたは批判的思考を持つディベーターです。建設的な反論を生成してください。"},
                    {"role": "user", "content": counter_prompt}
                ]
            )
            return counter.strip()
        except Exception as e:
            logger.error(
                "Failed to generate counter argument",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to generate counter argument",
                details={"error": str(e)}
            ) from e

    async def _generate_debate_summary(
        self,
        original_stance: str,
        counter_argument: str
    ) -> str:
        """ディベートのまとめを生成

        Args:
            original_stance: 元の主張
            counter_argument: 反論

        Returns:
            まとめテキスト
        """
        debate_summary_prompt = f"""以下の2つの主張について、簡潔なディベートのまとめを{self.settings.summary_min_length}字程度で生成してください。

【元の主張】
{original_stance}

【反論】
{counter_argument}

まとめ:"""

        try:
            summary = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "あなたは中立的な立場でディベートをまとめる司会者です。"},
                    {"role": "user", "content": debate_summary_prompt}
                ]
            )
            return summary.strip()
        except Exception as e:
            logger.error(
                "Failed to generate debate summary",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise LLMError(
                "Failed to generate debate summary",
                details={"error": str(e)}
            ) from e
