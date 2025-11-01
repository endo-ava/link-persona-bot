#!/usr/bin/env python3
"""
LLM API接続テストスクリプト
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトのルートをPYTHONPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.llm_client import get_llm_client


async def test_connection():
    """LLM API接続テスト"""

    print("=" * 60)
    print("LLM API 接続テスト")
    print("=" * 60)
    print()

    # 環境変数の確認
    print("📋 環境変数の確認:")
    print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'qwen (default)')}")
    print(f"  LLM_API_URL: {os.getenv('LLM_API_URL', '(using provider default)')}")
    print(f"  LLM_MODEL: {os.getenv('LLM_MODEL', '(using provider default)')}")

    # APIキーの確認（最初と最後の数文字のみ表示）
    api_key = os.getenv('LLM_API_KEY', '')
    if api_key:
        if len(api_key) > 10:
            masked_key = f"{api_key[:4]}...{api_key[-4:]}"
        else:
            masked_key = "***"
        print(f"  LLM_API_KEY: {masked_key}")
    else:
        print("  LLM_API_KEY: ❌ NOT SET")
        print()
        print("エラー: LLM_API_KEYが設定されていません。")
        print(".envファイルを確認してください。")
        return False

    print()

    try:
        # LLMクライアントの初期化
        print("🔧 LLMクライアントを初期化中...")
        client = get_llm_client()
        print(f"✅ 初期化成功")
        print(f"  プロバイダー: {client.provider}")
        print(f"  API URL: {client.api_url}")
        print(f"  モデル: {client.model}")
        print()

        # テストメッセージの送信
        print("📡 テストメッセージを送信中...")
        test_message = "こんにちは！接続テストです。「OK」とだけ返信してください。"

        messages = [
            {"role": "system", "content": "あなたは接続テスト用のアシスタントです。ユーザーの指示に従って簡潔に返信してください。"},
            {"role": "user", "content": test_message}
        ]

        response = await client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=50
        )

        print("✅ 接続成功！")
        print()
        print("📨 送信メッセージ:")
        print(f"  {test_message}")
        print()
        print("📬 受信レスポンス:")
        print(f"  {response}")
        print()
        print("=" * 60)
        print("✅ すべてのテストが正常に完了しました！")
        print("=" * 60)

        return True

    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        print()
        print("💡 ヒント: .envファイルの設定を確認してください。")
        return False

    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        print()
        print("💡 考えられる原因:")
        print("  1. APIキーが無効または期限切れ")
        print("  2. API URLが間違っている")
        print("  3. ネットワーク接続の問題")
        print("  4. プロバイダー側のサービス障害")

        # エラーの詳細を表示
        import traceback
        print()
        print("詳細なエラー情報:")
        print("-" * 60)
        traceback.print_exc()

        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
