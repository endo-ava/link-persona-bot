"""
Discord Bot メインファイル
"""

import logging
import os
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

from api.persona_loader import get_persona_loader
from api.llm_client import get_llm_client
from bot.api_client import get_api_client, APIClientError

# ロガー設定
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# Intentsの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容の取得を有効化


class PersonaBot(discord.Client):
    """ペルソナ機能を持つDiscord Bot

    責務:
    - Discord クライアントのライフサイクル管理
    - イベントルーティング（handlers への委譲）
    - Discord API との通信
    """

    def __init__(self) -> None:
        super().__init__(intents=intents)
        self.tree: app_commands.CommandTree = app_commands.CommandTree(self)

        # 依存関係の初期化
        from bot.state.conversation_manager import ConversationManager
        from bot.handlers import CommandHandler, MessageHandler

        self.conversation_manager = ConversationManager()
        self.persona_loader = get_persona_loader()
        self.llm_client = get_llm_client()
        self.api_client = get_api_client()

        # ハンドラーの初期化（依存性注入）
        self.command_handler = CommandHandler(
            conversation_manager=self.conversation_manager,
            persona_loader=self.persona_loader,
        )
        self.message_handler = MessageHandler(
            conversation_manager=self.conversation_manager,
            persona_loader=self.persona_loader,
            llm_client=self.llm_client,
            api_client=self.api_client,
        )

        logger.info("PersonaBot initialized")

    async def setup_hook(self) -> None:
        """起動時にコマンドを同期"""
        await self.tree.sync()
        logger.info("Command tree synced")

    async def on_ready(self) -> None:
        """Bot起動時の処理"""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        print(f"Available personas: {', '.join(self.persona_loader.list_persona_ids())}")
        print(f"API URL: {self.api_client.api_url}")

        # APIサーバーの接続確認
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_client.api_url}/health")
                if response.status_code == 200:
                    print("✓ API server is running")
                else:
                    print(f"⚠️  API server returned status code: {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to API server: {e}")
            print("   Make sure to start it with: uv run uvicorn api.main:app --reload")

        print("------")

        logger.info(
            "Bot ready",
            extra={
                "user": str(self.user),
                "user_id": self.user.id,
                "personas": self.persona_loader.list_persona_ids(),
            }
        )

    async def on_message(self, message: discord.Message) -> None:
        """メッセージ受信時の処理 - ルーティングのみ"""
        # 自分のメッセージは無視
        if message.author == self.user:
            return

        # コマンドは無視（スラッシュコマンドで処理）
        if message.content.startswith("/"):
            return

        try:
            # URL検出と自動要約（F101: Auto Persona Summarize）
            urls = self.message_handler.detect_urls(message.content)
            if urls:
                # 最初のURLのみ処理（複数URLは対応していない）
                await self._handle_url_message(message, urls[0])
                return

            # メンションされていない場合は無視
            if self.user not in message.mentions:
                return

            # メンション応答処理
            await self._handle_mention_message(message)

        except Exception as e:
            logger.error(
                "Error handling message",
                extra={"message_id": message.id, "error": str(e)},
                exc_info=True,
            )
            await message.channel.send("エラーが発生しました。")

    async def _handle_url_message(
        self,
        message: discord.Message,
        url: str,
    ) -> None:
        """URL検出メッセージを処理

        Args:
            message: Discordメッセージオブジェクト
            url: 検出されたURL
        """
        async with message.channel.typing():
            try:
                result = await self.message_handler.handle_url(
                    url=url,
                    channel_id=message.channel.id,
                    user_id=str(message.author.id),
                    guild_id=str(message.guild.id) if message.guild else None,
                )

                # Discord Embedを作成して送信
                embed = self._create_ingest_embed(result)
                await message.reply(embed=embed, mention_author=False)

            except APIClientError as e:
                logger.warning(
                    "URL ingestion failed",
                    extra={"url": url, "error": str(e)},
                )
                await message.channel.send(f"記事の取得に失敗しました: {str(e)}")

    async def _handle_mention_message(
        self,
        message: discord.Message,
    ) -> None:
        """メンション応答を処理

        Args:
            message: Discordメッセージオブジェクト
        """
        # メンション部分を除去
        content = self._extract_content_from_mention(message)

        async with message.channel.typing():
            try:
                response = await self.message_handler.handle_mention(
                    channel_id=message.channel.id,
                    content=content,
                )

                # ペルソナ情報を取得して整形
                persona_id = self.conversation_manager.get_persona(message.channel.id)
                if persona_id:
                    formatted = f"{response}\n\n-# ペルソナモード: {persona_id}"
                else:
                    formatted = response

                await message.reply(formatted, mention_author=False)

            except Exception as e:
                logger.error(
                    "Mention handling failed",
                    extra={"message_id": message.id, "error": str(e)},
                    exc_info=True,
                )
                await message.channel.send(f"エラーが発生しました: {str(e)}")

    def _extract_content_from_mention(self, message: discord.Message) -> str:
        """メンションを除去してコンテンツを抽出

        Args:
            message: Discordメッセージオブジェクト

        Returns:
            メンション除去後のコンテンツ
        """
        content = message.content
        content = content.replace(f"<@{self.user.id}>", "")
        content = content.replace(f"<@!{self.user.id}>", "")
        content = content.strip()
        return content if content else "何か話しかけてください。"

    def _create_ingest_embed(self, result) -> discord.Embed:
        """記事要約結果からEmbedを作成

        Args:
            result: IngestResponse

        Returns:
            Discord Embed
        """
        persona = result['persona']
        embed = discord.Embed(
            title=f"{persona['icon']} {persona['name']}の記事紹介",
            description=result['summary'],
            color=persona['color'],
            url=result['article_url'],
        )

        if result.get('article_title'):
            embed.add_field(
                name="📰 記事タイトル",
                value=result['article_title'],
                inline=False,
            )

        embed.add_field(
            name="🔗 リンク",
            value=result['article_url'],
            inline=False,
        )

        return embed


# Botインスタンスの作成
bot = PersonaBot()


@bot.tree.command(name="persona", description="ペルソナを設定または解除します")
@app_commands.describe(style="使用するペルソナのスタイル（例: sarcastic）または 'reset' で解除")
async def persona_command(interaction: discord.Interaction, style: Optional[str] = None) -> None:
    """
    /persona コマンド - ハンドラーに委譲

    - 引数なし: ドロップダウンメニューを表示（または現在の設定を表示）
    - 引数あり: 直接ペルソナを設定（後方互換性）
    - 'reset': ペルソナを解除
    """
    from bot.ui.persona_components import PersonaSelectView
    from bot.exceptions import PersonaNotFoundError

    channel_id = interaction.channel_id

    try:
        # Reset処理
        if style and style.lower() == "reset":
            message = bot.command_handler.handle_persona_reset(channel_id)
            await interaction.response.send_message(message)
            return

        # スタイル指定あり: 直接設定
        if style:
            try:
                embed = bot.command_handler.handle_persona_set(channel_id, style)
                await interaction.response.send_message(embed=embed)
            except PersonaNotFoundError as e:
                await interaction.response.send_message(str(e))
            return

        # スタイル指定なし: 現在のペルソナを表示 or 選択UIを表示
        current_embed = bot.command_handler.handle_persona_get(channel_id)
        view = PersonaSelectView(bot.conversation_manager, channel_id)

        if current_embed:
            # 現在のペルソナがある場合
            await interaction.response.send_message(embed=current_embed, view=view)
        else:
            # ペルソナ未設定の場合
            prompt_embed = bot.command_handler.create_persona_selection_embed()
            await interaction.response.send_message(embed=prompt_embed, view=view)

    except Exception as e:
        logger.error(
            "Persona command failed",
            extra={"channel_id": channel_id, "style": style, "error": str(e)},
            exc_info=True,
        )
        await interaction.response.send_message(
            "エラーが発生しました。",
            ephemeral=True,
        )


@bot.tree.command(name="debate", description="記事の主張に対する反論を生成します")
@app_commands.describe(url="記事のURL")
async def debate_command(interaction: discord.Interaction, url: str) -> None:
    """
    /debate コマンド
    記事の主張に対する反論を生成し、ディベート形式で返す（F202: Debate Mode）

    Args:
        interaction: Discordインタラクション
        url: 記事のURL
    """
    # URLの簡易バリデーション
    if not url.startswith(("http://", "https://")):
        await interaction.response.send_message(
            "❌ 有効なURLを指定してください（http://またはhttps://で始まる必要があります）",
            ephemeral=True,
        )
        return

    # 処理中メッセージを送信（5秒以内に応答する必要があるため）
    await interaction.response.send_message(
        "🤔 記事を分析してディベートを生成中...",
    )

    try:
        # TODO: 新しいAPIでは/debateは会話ベースに変更されているため、
        # 記事ベースのディベート機能は現在未実装
        await interaction.edit_original_response(
            content="申し訳ございません。ディベート機能は現在リファクタリング中のため一時的に利用できません。\n"
            "代わりに `/persona` コマンドでペルソナを設定し、そのペルソナと会話してみてください！"
        )

    except APIClientError as e:
        logger.warning(
            "Debate command failed (API error)",
            extra={"url": url, "error": str(e)},
        )
        await interaction.edit_original_response(
            content=f"❌ ディベート生成に失敗しました: {str(e)}"
        )

    except Exception as e:
        logger.error(
            "Unexpected error in debate_command",
            extra={"url": url, "error": str(e)},
            exc_info=True,
        )
        await interaction.edit_original_response(
            content=f"❌ 予期しないエラーが発生しました: {str(e) or type(e).__name__}"
        )


def main() -> None:
    """
    メインエントリーポイント：Discord Botを起動する

    環境変数 DISCORD_TOKEN から Bot トークンを読み込み、
    Discord への接続を確立して Bot を実行する。

    Raises:
        ValueError: DISCORD_TOKEN が設定されていない場合
    """
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    logger.info("Starting Discord Bot")
    bot.run(token)


if __name__ == "__main__":
    main()
