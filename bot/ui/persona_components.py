"""ペルソナ選択UIコンポーネント

Discord UIのViewとSelectコンポーネントを提供します。
"""

import logging
from typing import TYPE_CHECKING

import discord
from discord.ui import View, Select

from api.persona_loader import get_persona_loader
from bot.config import get_settings

if TYPE_CHECKING:
    from bot.state.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class PersonaSelectView(View):
    """ペルソナ選択用のドロップダウンメニューを持つView"""

    def __init__(self, conversation_manager: "ConversationManager", channel_id: int):
        """初期化

        Args:
            conversation_manager: 会話履歴マネージャー
            channel_id: チャンネルID
        """
        settings = get_settings()
        super().__init__(timeout=settings.persona_select_timeout)

        self.conversation_manager = conversation_manager
        self.channel_id = channel_id

        # ペルソナ選択ドロップダウンを作成
        select = PersonaSelect(conversation_manager, channel_id)
        self.add_item(select)

        logger.debug(
            "PersonaSelectView created",
            extra={"channel_id": channel_id, "timeout": settings.persona_select_timeout}
        )


class PersonaSelect(Select):
    """ペルソナを選択するドロップダウンメニュー"""

    def __init__(self, conversation_manager: "ConversationManager", channel_id: int):
        """初期化

        Args:
            conversation_manager: 会話履歴マネージャー
            channel_id: チャンネルID
        """
        self.conversation_manager = conversation_manager
        self.channel_id = channel_id
        self.persona_loader = get_persona_loader()
        self.settings = get_settings()

        # すべてのペルソナを取得してオプションを作成
        personas = self.persona_loader.get_all_personas()
        options = []

        for persona_id, persona in personas.items():
            # 説明文を最大文字数に制限
            description = persona.description
            if len(description) > self.settings.description_max_length:
                description = description[:self.settings.description_max_length]

            options.append(
                discord.SelectOption(
                    label=persona.name,
                    value=persona_id,
                    description=description,
                    emoji=persona.icon,
                )
            )

        # オプションをアルファベット順にソート（persona_idでソート）
        options.sort(key=lambda x: x.value)

        super().__init__(
            placeholder="ペルソナを選択してください...",
            min_values=1,
            max_values=1,
            options=options,
        )

        logger.debug(
            "PersonaSelect created",
            extra={"channel_id": channel_id, "persona_count": len(options)}
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """ユーザーが選択したときの処理

        Args:
            interaction: Discord インタラクション
        """
        selected_persona_id = self.values[0]
        persona = self.persona_loader.get_persona(selected_persona_id)

        logger.info(
            "Persona selected",
            extra={
                "channel_id": self.channel_id,
                "persona_id": selected_persona_id,
                "user_id": interaction.user.id
            }
        )

        if not persona:
            logger.error(
                "Selected persona not found",
                extra={"persona_id": selected_persona_id}
            )
            await interaction.response.send_message(
                "エラー: ペルソナが見つかりません。",
                ephemeral=True,
            )
            return

        # ペルソナを設定
        self.conversation_manager.set_persona(self.channel_id, selected_persona_id)

        # 会話履歴をクリア
        self.conversation_manager.clear_history(self.channel_id)

        # 確認メッセージを送信
        embed = discord.Embed(
            title="ペルソナ設定完了",
            description=f"{persona.get_display_name()} モードに切り替わりました。\n\n"
            f"**説明**: {persona.description}\n\n"
            f"このチャンネルで何か話しかけてみてください。\n"
            f"解除するには `/persona reset` を実行してください。",
            color=persona.color
        )
        embed.set_footer(text=f"Persona ID: {selected_persona_id}")

        await interaction.response.send_message(embed=embed)

        logger.info(
            "Persona activation confirmed",
            extra={"channel_id": self.channel_id, "persona_id": selected_persona_id}
        )


def create_persona_embed(persona_id: str, message: str) -> discord.Embed:
    """ペルソナ情報を含むEmbedを作成

    Args:
        persona_id: ペルソナID
        message: メッセージ内容

    Returns:
        Discord Embed
    """
    persona_loader = get_persona_loader()
    persona = persona_loader.get_persona(persona_id)

    if not persona:
        # フォールバック: デフォルトEmbed
        return discord.Embed(
            description=message,
            color=discord.Color.blue()
        )

    embed = discord.Embed(
        description=message,
        color=persona.color
    )
    embed.set_author(
        name=persona.get_display_name(),
        icon_url=None  # アイコンURLを設定する場合はここに
    )
    embed.set_footer(text=f"Persona: {persona.name}")

    return embed
