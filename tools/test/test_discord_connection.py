#!/usr/bin/env python3
"""
Discord Bot接続テストスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトのルートをPYTHONPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import discord
from discord.ext import commands


def test_discord_token():
    """Discordトークンの検証"""

    print("=" * 60)
    print("Discord Bot 接続テスト")
    print("=" * 60)
    print()

    # トークンの確認
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ エラー: DISCORD_TOKENが設定されていません。")
        print()
        print(".envファイルを確認してください：")
        print("  DISCORD_TOKEN=your_discord_bot_token_here")
        return False

    # トークンの表示（マスク）
    if len(token) > 10:
        masked_token = f"{token[:8]}...{token[-4:]}"
    else:
        masked_token = "***"
    print(f"📋 DISCORD_TOKEN: {masked_token}")
    print()

    # Intentsの設定
    intents = discord.Intents.default()
    intents.message_content = True

    # テスト用の簡易Botクラス
    class TestBot(discord.Client):
        def __init__(self):
            super().__init__(intents=intents)
            self.ready_event_fired = False

        async def on_ready(self):
            self.ready_event_fired = True
            print("✅ Discord接続成功！")
            print()
            print("📊 Bot情報:")
            print(f"  Bot名: {self.user.name}")
            print(f"  Bot ID: {self.user.id}")
            print(f"  参加サーバー数: {len(self.guilds)}")
            print()

            if self.guilds:
                print("📝 参加しているサーバー:")
                for guild in self.guilds:
                    print(f"  - {guild.name} (ID: {guild.id}, メンバー数: {guild.member_count})")
            else:
                print("⚠️  まだどのサーバーにも参加していません。")
                print()
                print("💡 Botを招待するには:")
                print(f"   https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=277025770496&scope=bot%20applications.commands")

            print()
            print("=" * 60)
            print("✅ 接続テスト完了！Botを停止します...")
            print("=" * 60)

            # テストが完了したのでBotを停止
            await self.close()

        async def on_error(self, event, *args, **kwargs):
            print(f"❌ エラーが発生しました: {event}")
            import traceback
            traceback.print_exc()

    print("🔧 Discord Botを初期化中...")
    bot = TestBot()

    try:
        print("🌐 Discordに接続中...")
        print("   (接続には数秒かかる場合があります)")
        print()

        # Botを起動（非同期で実行し、on_readyで自動停止）
        bot.run(token, log_handler=None)

        # on_readyが発火したか確認
        if bot.ready_event_fired:
            return True
        else:
            print("❌ 接続に失敗しました。")
            return False

    except discord.LoginFailure:
        print("❌ ログイン失敗: トークンが無効です。")
        print()
        print("💡 対処方法:")
        print("  1. Discord Developer Portalでトークンを再生成")
        print("  2. .envファイルのDISCORD_TOKENを更新")
        print()
        print("Discord Developer Portal:")
        print("  https://discord.com/developers/applications")
        return False

    except discord.PrivilegedIntentsRequired:
        print("❌ 特権インテント（Privileged Intents）が有効になっていません。")
        print()
        print("💡 対処方法:")
        print("  1. Discord Developer Portalでアプリケーションを開く")
        print("  2. 'Bot' タブに移動")
        print("  3. 'Privileged Gateway Intents' セクションで以下を有効化:")
        print("     - MESSAGE CONTENT INTENT")
        print("  4. 変更を保存してBotを再起動")
        return False

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        print()
        import traceback
        print("詳細なエラー情報:")
        print("-" * 60)
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_discord_token()
    sys.exit(0 if success else 1)
