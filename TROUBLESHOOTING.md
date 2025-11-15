# トラブルシューティングガイド

## よくある問題と解決方法

### 1. 「Unexpected error」が発生する

**症状:**
```
Error in handle_url_summary: Unexpected error:
```

**原因:**
- APIサーバーが起動していない（最も多い原因）
- API URLの設定が間違っている
- ネットワーク接続の問題

**解決方法:**

1. **APIサーバーが起動しているか確認**
   ```bash
   # 別のターミナルで実行
   uv run uvicorn api.main:app --reload
   ```

2. **Bot起動時のログを確認**
   ```
   ✓ API server is running      ← これが表示されればOK
   ❌ Cannot connect to API server  ← APIサーバーが起動していない
   ```

3. **環境変数を確認**
   ```bash
   # .envファイルを確認
   cat .env | grep API_URL

   # デフォルトは http://localhost:8000
   ```

### 2. 「記事の取得に失敗しました」エラー

**症状:**
```
❌ 記事の取得に失敗しました: Failed to fetch URL: Client error '403 Forbidden'
```

**原因:**
- 外部サイトがBotのアクセスをブロック
- ネットワークアクセスが制限されている
- JavaScriptレンダリングが必要なサイト（SPA）

**解決方法:**
- 静的HTMLのサイトを試す
- ローカルでテストする場合は、アクセス可能なサイトを使用
- User-Agentヘッダーは既に設定済み（api/fetcher.py）

### 3. 「LLM API key not found」エラー

**症状:**
```
ValueError: LLM API key not found. Set LLM_API_KEY environment variable.
```

**原因:**
- .envファイルが存在しない
- LLM_API_KEYが設定されていない

**解決方法:**
```bash
# 1. .env.exampleをコピー
cp .env.example .env

# 2. .envファイルを編集
nano .env  # または vim, code など

# 3. 以下を設定
LLM_API_KEY=your_actual_api_key_here
LLM_PROVIDER=qwen  # または openai など
```

### 4. Discord Botが応答しない

**症状:**
- URLを投稿してもBotが反応しない
- `/persona`コマンドが動作しない

**原因:**
- DISCORD_TOKENが設定されていない
- Botに必要な権限がない
- Intentsが有効化されていない

**解決方法:**

1. **環境変数を確認**
   ```bash
   cat .env | grep DISCORD_TOKEN
   ```

2. **Discord Developer Portalで確認**
   - Message Content Intentが有効か確認
   - Bot権限に `Send Messages`, `Read Message History` が含まれているか

3. **Botを再起動**
   ```bash
   # Ctrl+C で停止してから
   uv run python -m bot.main
   ```

### 5. エラーの詳細を確認する方法

**ターミナルの出力を確認:**
```bash
uv run python -m bot.main 2>&1 | tee bot.log
```

**重要なログ:**
- `Logged in as ...` - Bot起動成功
- `✓ API server is running` - API接続成功
- `Traceback` - エラーの詳細なスタックトレース

### デバッグモード

より詳しいログを出力したい場合：

```bash
# API側
export LOG_LEVEL=DEBUG
uv run uvicorn api.main:app --log-level debug

# Bot側（Python loggingを使用）
# bot/main.py の先頭に追加:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## サポート

問題が解決しない場合：
1. エラーの完全なスタックトレースを保存
2. 実行環境の情報を確認（`uv --version`, `python --version`）
3. GitHubのIssueに報告
