"""コマンドハンドリングサービス

スラッシュコマンドのビジネスロジックを処理します。
Discord API の詳細から分離された、テスト可能な実装を提供します。
"""

import logging
from typing import Optional

import discord

from api.persona_loader import PersonaLoader
from bot.state.conversation_manager import ConversationManager
from bot.exceptions import PersonaNotFoundError

logger = logging.getLogger(__name__)


class CommandHandler:
    """コマンドハンドリングサービス

    スラッシュコマンドのビジネスロジックを処理します。

    責務:
    - コマンドパラメータの検証
    - ペルソナ設定・解除
    - 会話履歴のクリア
    - Discord Embedの生成
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        persona_loader: PersonaLoader,
    ):
        """初期化

        Args:
            conversation_manager: 会話履歴マネージャー
            persona_loader: ペルソナローダー
        """
        self.conversation_manager = conversation_manager
        self.persona_loader = persona_loader

        logger.info("CommandHandler initialized")

    def handle_persona_set(
        self,
        channel_id: int,
        persona_id: str,
    ) -> discord.Embed:
        """ペルソナを設定

        Args:
            channel_id: チャンネルID
            persona_id: ペルソナID

        Returns:
            設定完了を示すEmbed

        Raises:
            PersonaNotFoundError: ペルソナが見つからない場合
        """
        # ペルソナの存在確認
        persona = self.persona_loader.get_persona(persona_id)
        if not persona:
            available_ids = ", ".join(self.persona_loader.list_persona_ids())
            logger.warning(
                "Persona not found",
                extra={"persona_id": persona_id, "available_ids": available_ids}
            )
            raise PersonaNotFoundError(
                f"ペルソナ `{persona_id}` が見つかりません。\n"
                f"利用可能なペルソナ: {available_ids}",
                details={"persona_id": persona_id, "channel_id": channel_id}
            )

        # ペルソナを設定
        self.conversation_manager.set_persona(channel_id, persona_id)

        # 会話履歴をクリア（新しいペルソナで新しい会話を開始）
        self.conversation_manager.clear_history(channel_id)

        logger.info(
            "Persona set successfully",
            extra={"channel_id": channel_id, "persona_id": persona_id}
        )

        # 確認メッセージEmbedを作成
        embed = discord.Embed(
            title="ペルソナ設定完了",
            description=(
                f"{persona.get_display_name()} モードに切り替わりました。\n\n"
                f"**説明**: {persona.description}\n\n"
                f"このチャンネルで何か話しかけてみてください。\n"
                f"解除するには `/persona reset` を実行してください。"
            ),
            color=persona.color,
        )
        embed.set_footer(text=f"Persona ID: {persona_id}")

        return embed

    def handle_persona_reset(self, channel_id: int) -> str:
        """ペルソナを解除

        Args:
            channel_id: チャンネルID

        Returns:
            解除完了メッセージ
        """
        persona_id = self.conversation_manager.get_persona(channel_id)

        if not persona_id:
            logger.info(
                "No persona to reset",
                extra={"channel_id": channel_id}
            )
            return "ペルソナが設定されていません。"

        # ペルソナ情報を取得（表示用）
        persona = self.persona_loader.get_persona(persona_id)
        display_name = persona.get_display_name() if persona else "不明なペルソナ"

        # ペルソナを解除（会話履歴もクリア）
        self.conversation_manager.reset_persona(channel_id)

        logger.info(
            "Persona reset completed",
            extra={"channel_id": channel_id, "old_persona_id": persona_id}
        )

        return f"ペルソナ {display_name} を解除しました。"

    def handle_persona_get(
        self,
        channel_id: int,
    ) -> Optional[discord.Embed]:
        """現在のペルソナを取得

        Args:
            channel_id: チャンネルID

        Returns:
            現在のペルソナ情報のEmbed（未設定の場合はNone）
        """
        persona_id = self.conversation_manager.get_persona(channel_id)

        if not persona_id:
            logger.debug(
                "No persona set for channel",
                extra={"channel_id": channel_id}
            )
            return None

        persona = self.persona_loader.get_persona(persona_id)

        if not persona:
            logger.error(
                "Persona ID in state but not found in loader",
                extra={"channel_id": channel_id, "persona_id": persona_id}
            )
            # 状態が不整合な場合でも、ユーザーには適切なメッセージを返す
            return discord.Embed(
                title="エラー",
                description=f"ペルソナ `{persona_id}` の情報が見つかりません。",
                color=discord.Color.red(),
            )

        # 現在のペルソナ情報を埋め込みで作成
        embed = discord.Embed(
            title="現在のペルソナ",
            description=(
                f"{persona.get_display_name()}\n\n"
                f"**説明**: {persona.description}\n\n"
                f"別のペルソナに変更する場合は下のメニューから選択してください。\n"
                f"解除するには `/persona reset` を実行してください。"
            ),
            color=persona.color,
        )
        embed.set_footer(text=f"Persona ID: {persona_id}")

        logger.debug(
            "Retrieved current persona",
            extra={"channel_id": channel_id, "persona_id": persona_id}
        )

        return embed

    def create_persona_selection_embed(self) -> discord.Embed:
        """ペルソナ選択プロンプト用のEmbedを作成

        Returns:
            ペルソナ選択を促すEmbed
        """
        return discord.Embed(
            title="ペルソナ選択",
            description=(
                "使用するペルソナを下のメニューから選択してください。\n"
                "各ペルソナには独自の個性と話し方があります。"
            ),
            color=discord.Color.blue(),
        )
