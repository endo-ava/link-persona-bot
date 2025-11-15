"""メッセージハンドリングサービス

メッセージイベントのビジネスロジックを処理します。
Discord メッセージオブジェクトの処理から分離された実装を提供します。
"""

import logging
import re
from typing import Optional

from api.persona_loader import PersonaLoader
from api.llm_client import LLMClient
from bot.api_client import APIClient, APIClientError
from bot.state.conversation_manager import ConversationManager
from bot.models import IngestResponse
from bot.exceptions import MessageHandlingError, URLDetectionError

logger = logging.getLogger(__name__)

# URL検出用の正規表現パターン
URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)


class MessageHandler:
    """メッセージハンドリングサービス

    メッセージイベントのビジネスロジックを処理します。

    責務:
    - URL検出と記事要約
    - メンション応答の生成
    - 会話履歴の管理
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        persona_loader: PersonaLoader,
        llm_client: LLMClient,
        api_client: APIClient,
    ):
        """初期化

        Args:
            conversation_manager: 会話履歴マネージャー
            persona_loader: ペルソナローダー
            llm_client: LLMクライアント
            api_client: APIクライアント
        """
        self.conversation_manager = conversation_manager
        self.persona_loader = persona_loader
        self.llm_client = llm_client
        self.api_client = api_client

        logger.info("MessageHandler initialized")

    async def handle_mention(
        self,
        channel_id: int,
        content: str,
    ) -> str:
        """メンション応答を生成

        Args:
            channel_id: チャンネルID
            content: メッセージ内容（メンション部分は除去済み）

        Returns:
            応答メッセージ

        Raises:
            MessageHandlingError: 応答生成に失敗した場合
        """
        persona_id = self.conversation_manager.get_persona(channel_id)

        logger.info(
            "Handling mention",
            extra={
                "channel_id": channel_id,
                "persona_id": persona_id,
                "content_length": len(content),
            }
        )

        try:
            if persona_id:
                # ペルソナモードで応答
                response = await self._respond_with_persona(
                    channel_id=channel_id,
                    persona_id=persona_id,
                    content=content,
                )
            else:
                # ペルソナなしで通常応答
                response = await self._respond_without_persona(content)

            logger.info(
                "Mention response generated",
                extra={
                    "channel_id": channel_id,
                    "persona_id": persona_id,
                    "response_length": len(response),
                }
            )

            return response

        except Exception as e:
            logger.error(
                "Failed to handle mention",
                extra={
                    "channel_id": channel_id,
                    "persona_id": persona_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise MessageHandlingError(
                "メンション応答の生成に失敗しました",
                details={"channel_id": channel_id, "persona_id": persona_id}
            ) from e

    async def _respond_with_persona(
        self,
        channel_id: int,
        persona_id: str,
        content: str,
    ) -> str:
        """ペルソナに基づいて応答を生成（内部メソッド）

        Args:
            channel_id: チャンネルID
            persona_id: ペルソナID
            content: メッセージ内容

        Returns:
            応答メッセージ
        """
        persona = self.persona_loader.get_persona(persona_id)
        if not persona:
            logger.error(
                "Persona not found during response",
                extra={"persona_id": persona_id}
            )
            return "エラー: ペルソナが見つかりません。"

        # 会話履歴を取得
        history = self.conversation_manager.get_history(channel_id)

        # LLM APIで応答生成
        response = await self.llm_client.generate_persona_response(
            system_prompt=persona.get_system_message(),
            user_message=content,
            conversation_history=history,
        )

        # 会話履歴を更新
        self.conversation_manager.add_message(channel_id, "user", content)
        self.conversation_manager.add_message(channel_id, "assistant", response)

        return response

    async def _respond_without_persona(self, content: str) -> str:
        """ペルソナなしで通常応答を生成（内部メソッド）

        Args:
            content: メッセージ内容

        Returns:
            応答メッセージ
        """
        # LLM APIで応答生成（システムプロンプトなし）
        response = await self.llm_client.generate_persona_response(
            system_prompt="あなたは親切で役に立つアシスタントです。",
            user_message=content,
            conversation_history=[],
        )

        return response

    async def handle_url(
        self,
        url: str,
        channel_id: int,
        user_id: str,
        guild_id: Optional[str] = None,
    ) -> IngestResponse:
        """URLを要約

        Args:
            url: 記事URL
            channel_id: チャンネルID
            user_id: ユーザーID
            guild_id: サーバーID（DMの場合はNone）

        Returns:
            記事要約結果

        Raises:
            APIClientError: API呼び出しに失敗した場合
            URLDetectionError: URL処理に失敗した場合
        """
        # チャンネルで設定されているペルソナを取得（なければNone）
        persona_id = self.conversation_manager.get_persona(channel_id)

        logger.info(
            "Handling URL",
            extra={
                "url": url,
                "channel_id": channel_id,
                "persona_id": persona_id,
                "user_id": user_id,
                "guild_id": guild_id,
            }
        )

        try:
            # /ingest エンドポイントを呼び出し
            result = await self.api_client.ingest_url(
                url=url,
                persona_id=persona_id,
                user_id=user_id,
                guild_id=guild_id,
            )

            logger.info(
                "URL processed successfully",
                extra={
                    "url": url,
                    "persona_id": result['persona']['name'],
                    "article_title": result.get('article_title', 'N/A'),
                }
            )

            return result

        except APIClientError as e:
            logger.warning(
                "API client error during URL handling",
                extra={"url": url, "error": str(e)},
            )
            raise  # Re-raise to let caller handle

        except Exception as e:
            logger.error(
                "Unexpected error during URL handling",
                extra={"url": url, "error": str(e)},
                exc_info=True,
            )
            raise URLDetectionError(
                "URL処理中にエラーが発生しました",
                details={"url": url}
            ) from e

    def detect_urls(self, content: str) -> list[str]:
        """メッセージからURLを検出

        Args:
            content: メッセージ内容

        Returns:
            検出されたURLのリスト
        """
        urls = URL_PATTERN.findall(content)

        logger.debug(
            "URL detection",
            extra={"content_length": len(content), "urls_found": len(urls)}
        )

        return urls
