"""
Discord Bot メインファイル
"""

import os
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ui import View, Select
from dotenv import load_dotenv

from api.persona_loader import get_persona_loader, Persona
from api.llm_client import get_llm_client

# 環境変数の読み込み
load_dotenv()

# Intentsの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容の取得を有効化


class PersonaSelectView(View):
    """ペルソナ選択用のドロップダウンメニューを持つView"""

    def __init__(self, bot_instance: "PersonaBot", channel_id: int):
        super().__init__(timeout=180)  # 3分でタイムアウト
        self.bot_instance = bot_instance
        self.channel_id = channel_id

        # ペルソナ選択ドロップダウンを作成
        select = PersonaSelect(bot_instance, channel_id)
        self.add_item(select)


class PersonaSelect(Select):
    """ペルソナを選択するドロップダウンメニュー"""

    def __init__(self, bot_instance: "PersonaBot", channel_id: int):
        self.bot_instance = bot_instance
        self.channel_id = channel_id

        # すべてのペルソナを取得してオプションを作成
        personas = bot_instance.persona_loader.get_all_personas()
        options = []

        for persona_id, persona in personas.items():
            options.append(
                discord.SelectOption(
                    label=persona.name,
                    value=persona_id,
                    description=persona.description[:100],  # Discordの制限: 最大100文字
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

    async def callback(self, interaction: discord.Interaction) -> None:
        """ユーザーが選択したときの処理"""
        selected_persona_id = self.values[0]
        persona = self.bot_instance.persona_loader.get_persona(selected_persona_id)

        if not persona:
            await interaction.response.send_message(
                "エラー: ペルソナが見つかりません。",
                ephemeral=True,
            )
            return

        # ペルソナを設定
        self.bot_instance.channel_personas[self.channel_id] = selected_persona_id

        # 会話履歴をクリア
        if self.channel_id in self.bot_instance.conversation_history:
            self.bot_instance.conversation_history[self.channel_id] = []

        # 確認メッセージを送信
        embed = discord.Embed(
            title="ペルソナ設定完了",
            description=f"{persona.get_display_name()} モードに切り替わりました。\n\n"
            f"**説明**: {persona.description}\n\n"
            f"このチャンネルで何か話しかけてみてください。\n"
            f"解除するには `/persona reset` を実行してください。",
            color=persona.color,
        )

        await interaction.response.send_message(embed=embed)

        # メニューを無効化（再利用防止）
        self.disabled = True
        await interaction.message.edit(view=self.view)


class PersonaBot(discord.Client):
    """ペルソナ機能を持つDiscord Bot"""

    def __init__(self) -> None:
        super().__init__(intents=intents)
        self.tree: app_commands.CommandTree = app_commands.CommandTree(self)

        # ペルソナとLLMクライアントの初期化
        from api.persona_loader import PersonaLoader
        from api.llm_client import LLMClient

        self.persona_loader: PersonaLoader = get_persona_loader()
        self.llm_client: LLMClient = get_llm_client()

        # チャンネルごとのペルソナ設定を保持
        self.channel_personas: Dict[int, str] = {}

        # チャンネルごとの会話履歴を保持（最大20件）
        self.conversation_history: Dict[int, List[Dict[str, str]]] = {}

    async def setup_hook(self) -> None:
        """起動時にコマンドを同期"""
        await self.tree.sync()

    async def on_ready(self) -> None:
        """Bot起動時の処理"""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        print(f"Available personas: {', '.join(self.persona_loader.list_persona_ids())}")

    async def on_message(self, message: discord.Message) -> None:
        """メッセージ受信時の処理"""
        # 自分のメッセージは無視
        if message.author == self.user:
            return

        # コマンドは無視（スラッシュコマンドで処理）
        if message.content.startswith("/"):
            return

        # メンションされていない場合は無視
        if self.user not in message.mentions:
            return

        # メンション部分を除去したメッセージを取得（両形式に対応）
        content = message.content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
        if not content:
            content = "何か話しかけてください。"

        # このチャンネルでペルソナが設定されているか確認
        channel_id = message.channel.id
        if channel_id in self.channel_personas:
            # ペルソナモードで応答
            await self.respond_with_persona(message, channel_id, content)
        else:
            # ペルソナなしで通常応答
            await self.respond_without_persona(message, content)

    async def respond_with_persona(self, message: discord.Message, channel_id: int, content: str) -> None:
        """ペルソナに基づいてメッセージに応答"""
        persona_id = self.channel_personas[channel_id]
        persona = self.persona_loader.get_persona(persona_id)

        if not persona:
            await message.channel.send("エラー: ペルソナが見つかりません。")
            return

        # タイピングインジケーターを表示
        async with message.channel.typing():
            try:
                # 会話履歴を取得
                history = self.conversation_history.get(channel_id, [])

                # LLM APIで応答生成
                response = await self.llm_client.generate_persona_response(
                    system_prompt=persona.get_system_message(),
                    user_message=content,
                    conversation_history=history,
                )

                # 会話履歴を更新
                if channel_id not in self.conversation_history:
                    self.conversation_history[channel_id] = []

                self.conversation_history[channel_id].append(
                    {"role": "user", "content": content}
                )
                self.conversation_history[channel_id].append(
                    {"role": "assistant", "content": response}
                )

                # 履歴が10件を超えたら古いものから削除
                if len(self.conversation_history[channel_id]) > 20:
                    self.conversation_history[channel_id] = self.conversation_history[
                        channel_id
                    ][-20:]

                # 通常のメッセージとして送信（ペルソナ名を小さく表示）
                formatted_response = f"{response}\n\n-# ペルソナモード: {persona_id}"

                await message.reply(formatted_response, mention_author=False)

            except Exception as e:
                await message.channel.send(f"エラーが発生しました: {str(e)}")
                print(f"Error in respond_with_persona: {e}")

    async def respond_without_persona(self, message: discord.Message, content: str) -> None:
        """ペルソナなしで通常応答"""
        # タイピングインジケーターを表示
        async with message.channel.typing():
            try:
                # LLM APIで応答生成（システムプロンプトなし）
                response = await self.llm_client.generate_persona_response(
                    system_prompt="あなたは親切で役に立つアシスタントです。",
                    user_message=content,
                    conversation_history=[],
                )

                # 通常のメッセージとして返信
                await message.reply(response, mention_author=False)

            except Exception as e:
                await message.channel.send(f"エラーが発生しました: {str(e)}")
                print(f"Error in respond_without_persona: {e}")


# Botインスタンスの作成
bot = PersonaBot()


@bot.tree.command(name="persona", description="ペルソナを設定または解除します")
@app_commands.describe(style="使用するペルソナのスタイル（例: sarcastic）または 'reset' で解除")
async def persona_command(interaction: discord.Interaction, style: Optional[str] = None) -> None:
    """
    /persona コマンド
    ペルソナを設定または解除する

    - 引数なし: ドロップダウンメニューを表示（または現在の設定を表示）
    - 引数あり: 直接ペルソナを設定（後方互換性）
    - 'reset': ペルソナを解除
    """
    channel_id = interaction.channel_id

    # "reset" で解除
    if style and style.lower() == "reset":
        if channel_id in bot.channel_personas:
            old_persona = bot.persona_loader.get_persona(bot.channel_personas[channel_id])
            old_display_name = old_persona.get_display_name() if old_persona else "不明なペルソナ"
            del bot.channel_personas[channel_id]
            # 会話履歴もクリア
            if channel_id in bot.conversation_history:
                del bot.conversation_history[channel_id]
            await interaction.response.send_message(
                f"ペルソナ {old_display_name} を解除しました。"
            )
        else:
            await interaction.response.send_message("ペルソナが設定されていません。")
        return

    # スタイルが指定されている場合は直接設定（後方互換性）
    if style:
        persona = bot.persona_loader.get_persona(style)
        if not persona:
            available = ", ".join(bot.persona_loader.list_persona_ids())
            await interaction.response.send_message(
                f"ペルソナ `{style}` が見つかりません。\n"
                f"利用可能なペルソナ: {available}"
            )
            return

        # ペルソナを設定
        bot.channel_personas[channel_id] = style

        # 会話履歴をクリア
        if channel_id in bot.conversation_history:
            bot.conversation_history[channel_id] = []

        # 確認メッセージ
        embed = discord.Embed(
            title="ペルソナ設定完了",
            description=f"{persona.get_display_name()} モードに切り替わりました。\n\n"
            f"**説明**: {persona.description}\n\n"
            f"このチャンネルで何か話しかけてみてください。\n"
            f"解除するには `/persona reset` を実行してください。",
            color=persona.color,
        )

        await interaction.response.send_message(embed=embed)
        return

    # スタイルが指定されていない場合
    # すでにペルソナが設定されている場合は現在の設定を表示し、ドロップダウンも表示
    if channel_id in bot.channel_personas:
        current_persona_id = bot.channel_personas[channel_id]
        persona = bot.persona_loader.get_persona(current_persona_id)

        # 現在のペルソナ情報を埋め込みで表示
        embed = discord.Embed(
            title="現在のペルソナ",
            description=f"{persona.get_display_name()}\n\n"
            f"**説明**: {persona.description}\n\n"
            f"別のペルソナに変更する場合は下のメニューから選択してください。\n"
            f"解除するには `/persona reset` を実行してください。",
            color=persona.color,
        )

        # ドロップダウンメニューを表示
        view = PersonaSelectView(bot, channel_id)
        await interaction.response.send_message(embed=embed, view=view)
    else:
        # ペルソナが設定されていない場合はドロップダウンメニューのみ表示
        embed = discord.Embed(
            title="ペルソナ選択",
            description="使用するペルソナを下のメニューから選択してください。\n"
            "各ペルソナには独自の個性と話し方があります。",
            color=discord.Color.blue(),
        )

        view = PersonaSelectView(bot, channel_id)
        await interaction.response.send_message(embed=embed, view=view)


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

    bot.run(token)


if __name__ == "__main__":
    main()
