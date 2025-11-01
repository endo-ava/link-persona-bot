# Koyebデプロイガイド

Link Persona BotをKoyebにデプロイする完全ガイドです。

## 目次

- [前提条件](#前提条件)
- [1. Discord Bot のセットアップ](#1-discord-bot-のセットアップ)
- [2. LLM API のセットアップ](#2-llm-api-のセットアップ)
- [3. Koyeb でのデプロイ](#3-koyeb-でのデプロイ)
- [4. 動作確認](#4-動作確認)
- [5. トラブルシューティング](#5-トラブルシューティング)
- [6. 継続的デプロイ](#6-継続的デプロイ)
- [7. コスト管理](#7-コスト管理)

---

## 前提条件

デプロイを開始する前に、以下を準備してください:

- ✅ GitHubアカウント（リポジトリが既にプッシュ済み）
- ✅ Koyebアカウント（無料登録: https://www.koyeb.com/）
- ✅ Discordアカウント
- ✅ LLM APIキー（Qwen, OpenAI, OpenRouter等）

---

## 1. Discord Bot のセットアップ

### 1.1 Botアプリケーションの作成

1. **Discord Developer Portalにアクセス**
   - https://discord.com/developers/applications

2. **新しいアプリケーションを作成**
   - 「New Application」ボタンをクリック
   - アプリケーション名を入力（例: `Link Persona Bot`）
   - 「Create」をクリック

3. **Bot情報の設定**
   - 左メニューから「Bot」を選択
   - 「Add Bot」をクリック（初回のみ）
   - Bot名とアイコンを設定（オプション）

### 1.2 Botトークンの取得

1. **トークンを取得**
   - Botページで「Reset Token」をクリック
   - 表示されたトークンを**安全な場所にコピー**
   - ⚠️ このトークンは二度と表示されません

```bash
# トークンの例（実際のトークンではありません - ダミー）
YOUR_BOT_TOKEN_HERE.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 1.3 Bot権限の設定

1. **Privileged Gateway Intentsを有効化**
   - Botページを下にスクロール
   - 「Privileged Gateway Intents」セクションで以下を有効化:
     - ✅ `MESSAGE CONTENT INTENT`（必須）
     - ✅ `SERVER MEMBERS INTENT`（オプション）
     - ✅ `PRESENCE INTENT`（オプション）

2. **変更を保存**
   - 「Save Changes」をクリック

### 1.4 Botの招待

1. **OAuth2 URL Generatorを使用**
   - 左メニューから「OAuth2」→「URL Generator」を選択

2. **Scopesを選択**
   - ✅ `bot`
   - ✅ `applications.commands`

3. **Bot Permissionsを選択**
   - ✅ `Send Messages`
   - ✅ `Send Messages in Threads`
   - ✅ `Embed Links`
   - ✅ `Attach Files`
   - ✅ `Read Message History`
   - ✅ `Use Slash Commands`
   - ✅ `Add Reactions`（オプション）

4. **招待URLをコピー**
   - ページ下部に生成されたURLをコピー
   - ブラウザで開き、Botを招待するサーバーを選択
   - 「認証」をクリック

```
生成されるURLの例:
https://discord.com/api/oauth2/authorize?client_id=123456789012345678&permissions=277025770496&scope=bot%20applications.commands
```

---

## 2. LLM API のセットアップ

### オプション1: Qwen（Alibaba Cloud Dashscope）

**特徴:**
- 高品質な中国語・英語対応
- 無料枠あり（月100万トークン）
- 比較的安価

**セットアップ手順:**

1. **Dashscope コンソールにアクセス**
   - https://dashscope.console.aliyun.com/

2. **アカウント作成**
   - Alibaba Cloudアカウントを作成（国際対応）
   - メールアドレスで登録可能

3. **APIキーを取得**
   - ダッシュボードから「API Key Management」を選択
   - 「Create API Key」をクリック
   - 生成されたキーをコピー

4. **環境変数設定値**
   ```bash
   LLM_PROVIDER=qwen
   LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
   LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   LLM_MODEL=qwen-plus
   ```

**利用可能なモデル:**
- `qwen-turbo`: 最速、低コスト
- `qwen-plus`: バランス型（推奨）
- `qwen-max`: 最高品質、高コスト
- `qwen-long`: 長文対応（最大100万トークン）

### オプション2: OpenAI

**特徴:**
- 最も有名で安定
- GPT-4, GPT-3.5-turbo等
- 比較的高コスト

**セットアップ手順:**

1. **OpenAI Platformにアクセス**
   - https://platform.openai.com/

2. **APIキーを取得**
   - https://platform.openai.com/api-keys
   - 「Create new secret key」をクリック
   - キーをコピー

3. **課金設定**
   - クレジットカードを登録
   - 使用制限を設定（推奨）

4. **環境変数設定値**
   ```bash
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
   LLM_API_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-3.5-turbo
   ```

**利用可能なモデル:**
- `gpt-3.5-turbo`: 低コスト、高速
- `gpt-4`: 高品質、高コスト
- `gpt-4-turbo`: GPT-4の高速版

### オプション3: OpenRouter（推奨）

**特徴:**
- 複数のLLMプロバイダーを統一API経由で利用
- Claude, GPT-4, Gemini, Llama等
- 柔軟なモデル切り替え
- 従量課金で無駄がない

**セットアップ手順:**

1. **OpenRouterにアクセス**
   - https://openrouter.ai/

2. **アカウント作成**
   - GitHubまたはGoogleアカウントで登録

3. **APIキーを取得**
   - https://openrouter.ai/keys
   - 「Create Key」をクリック
   - キーをコピー

4. **クレジットをチャージ**
   - https://openrouter.ai/credits
   - 最低$5からチャージ可能

5. **環境変数設定値**
   ```bash
   LLM_PROVIDER=openrouter
   LLM_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
   LLM_API_URL=https://openrouter.ai/api/v1
   LLM_MODEL=openai/gpt-3.5-turbo
   LLM_EXTRA_HEADER_HTTP_REFERER=https://github.com/endo-ava/link-persona-bot
   LLM_EXTRA_HEADER_X_TITLE=Link Persona Bot
   ```

**利用可能なモデル例:**
- `openai/gpt-3.5-turbo`: OpenAI GPT-3.5
- `openai/gpt-4`: OpenAI GPT-4
- `anthropic/claude-3-opus`: Anthropic Claude 3 Opus
- `google/gemini-pro`: Google Gemini Pro
- `meta-llama/llama-3-70b-instruct`: Meta Llama 3
- `qwen/qwen-2-72b-instruct`: Alibaba Qwen 2

モデル一覧: https://openrouter.ai/models

---

## 3. Koyeb でのデプロイ

### 方法A: Webコンソール（推奨）

#### 3.1 Koyebアカウントの作成

1. **Koyebにアクセス**
   - https://www.koyeb.com/

2. **アカウント作成**
   - 「Sign Up」をクリック
   - GitHubアカウントで登録（推奨）

3. **ダッシュボードにアクセス**
   - https://app.koyeb.com/

#### 3.2 GitHub連携

1. **GitHub連携を許可**
   - 初回ログイン時にGitHub連携を許可
   - リポジトリへのアクセス権限を付与

2. **リポジトリを選択**
   - `endo-ava/link-persona-bot`を選択
   - またはすべてのリポジトリへのアクセスを許可

#### 3.3 アプリケーションの作成

1. **新しいアプリを作成**
   - ダッシュボードで「Create App」をクリック

2. **デプロイ方法を選択**
   - 「GitHub」を選択

3. **リポジトリを選択**
   - リポジトリ: `endo-ava/link-persona-bot`
   - ブランチ: `main`
   - 「Next」をクリック

#### 3.4 ビルド設定

1. **Builder設定**
   ```
   Builder: Dockerfile
   Dockerfile path: ./Dockerfile
   ```

2. **ビルドコマンド（不要）**
   - Dockerfileを使用するため、ビルドコマンドは不要

3. **「Next」をクリック**

#### 3.5 環境変数の設定

1. **Environment Variables セクション**
   - 「Add Variable」をクリック

2. **Discord設定**
   ```
   Name: DISCORD_TOKEN
   Value: <Discord Botトークン>
   Secret: ✅（チェックを入れる）
   ```

3. **LLM設定（Qwenの例）**
   ```
   Name: LLM_PROVIDER
   Value: qwen

   Name: LLM_API_KEY
   Value: <Qwen APIキー>
   Secret: ✅

   Name: LLM_API_URL
   Value: https://dashscope.aliyuncs.com/compatible-mode/v1

   Name: LLM_MODEL
   Value: qwen-plus
   ```

4. **その他の設定**
   ```
   Name: ENV
   Value: production
   ```

**OpenRouterを使う場合の追加設定:**
```
Name: LLM_EXTRA_HEADER_HTTP_REFERER
Value: https://github.com/endo-ava/link-persona-bot

Name: LLM_EXTRA_HEADER_X_TITLE
Value: Link Persona Bot
```

#### 3.6 インスタンス設定

1. **Instance Type**
   - `Free` を選択（512MB RAM, 2GB Disk）

2. **Regions**
   - `Washington, D.C. (US East)` を選択（推奨）
   - または最も近いリージョンを選択

3. **Scaling**
   ```
   Min instances: 1
   Max instances: 1
   ```
   - Discord Botは常時起動が必要

4. **「Next」をクリック**

#### 3.7 サービス設定

1. **Ports**
   ```
   Port: 8000
   Protocol: HTTP
   ```

2. **Health Checks**
   ```
   Path: /health
   Protocol: HTTP
   Port: 8000
   ```

3. **App Name**
   ```
   App name: link-persona-bot
   Service name: api
   ```

4. **「Deploy」をクリック**

#### 3.8 デプロイの完了

1. **ビルドの進行状況を確認**
   - ビルドログが表示される
   - 通常2-3分で完了

2. **デプロイ完了を確認**
   - ステータスが「Running」になるのを待つ
   - 緑色のチェックマークが表示される

3. **URLを確認**
   - 割り当てられたURL（例: `https://link-persona-bot-endo-ava.koyeb.app`）

### 方法B: Koyeb CLI

#### 3.1 CLIのインストール

```bash
# macOS/Linux
curl -fsSL https://cli.koyeb.com/install.sh | sh

# パスを通す（必要に応じて）
export PATH="$HOME/.koyeb/bin:$PATH"

# インストール確認
koyeb version
```

#### 3.2 CLIでログイン

```bash
# ログイン
koyeb login

# ブラウザが開き、認証を求められる
# 認証完了後、ターミナルに戻る

# 認証確認
koyeb profile show
```

#### 3.3 Secretsの作成

```bash
# Discord トークン
koyeb secrets create discord-token \
  --value "YOUR_DISCORD_BOT_TOKEN"

# LLM APIキー
koyeb secrets create llm-api-key \
  --value "YOUR_LLM_API_KEY"

# Secrets一覧を確認
koyeb secrets list
```

#### 3.4 アプリのデプロイ

```bash
# Qwenを使う場合
koyeb app init link-persona-bot \
  --git github.com/endo-ava/link-persona-bot \
  --git-branch main \
  --git-builder dockerfile \
  --ports 8000:http \
  --routes /:8000 \
  --env DISCORD_TOKEN=@discord-token \
  --env LLM_PROVIDER=qwen \
  --env LLM_API_KEY=@llm-api-key \
  --env LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --env LLM_MODEL=qwen-plus \
  --env ENV=production \
  --instance-type free \
  --regions was \
  --scale-min 1 \
  --scale-max 1

# デプロイ状況を確認
koyeb app get link-persona-bot

# ログをフォロー
koyeb app logs link-persona-bot --follow
```

---

## 4. 動作確認

### 4.1 ヘルスチェック

```bash
# Koyeb URLを確認
KOYEB_URL="https://link-persona-bot-endo-ava.koyeb.app"

# ヘルスチェック
curl ${KOYEB_URL}/health

# 期待されるレスポンス:
# {"status":"ok"}
```

### 4.2 Discord Botの確認

1. **Botのオンライン状態を確認**
   - Discordで招待したサーバーを開く
   - メンバーリストでBotがオンライン（緑色）になっているか確認

2. **スラッシュコマンドのテスト**
   ```
   # チャットで入力
   /persona

   # 期待される動作:
   # 利用可能なペルソナの一覧が表示される
   ```

3. **ペルソナモードのテスト**
   ```
   # ペルソナを設定
   /persona sarcastic

   # Botをメンション
   @Link Persona Bot こんにちは！

   # 期待される動作:
   # 毒舌ジャーナリストのペルソナで応答が返る
   ```

4. **会話の継続**
   ```
   @Link Persona Bot AIについてどう思う？

   # 期待される動作:
   # 会話履歴を保持しながら、ペルソナで応答
   ```

5. **ペルソナのリセット**
   ```
   /persona reset

   # 期待される動作:
   # ペルソナモードが解除される
   ```

### 4.3 ログの確認

```bash
# Koyeb CLI でログを確認
koyeb app logs link-persona-bot --tail 50

# または Webコンソールで確認
# https://app.koyeb.com/apps/link-persona-bot/logs
```

---

## 5. トラブルシューティング

### 問題1: Botがオンラインにならない

**症状:**
- DiscordでBotがオフライン（灰色）のまま

**原因と解決策:**

1. **トークンが正しくない**
   ```bash
   # Koyeb環境変数を確認
   koyeb secrets get discord-token

   # 再設定
   koyeb secrets update discord-token --value "NEW_TOKEN"
   koyeb app redeploy link-persona-bot
   ```

2. **MESSAGE CONTENT INTENTが無効**
   - Discord Developer Portalで設定を確認
   - Bot → Privileged Gateway Intents → MESSAGE CONTENT INTENT を有効化

3. **デプロイに失敗している**
   ```bash
   # ログを確認
   koyeb app logs link-persona-bot --tail 100

   # ビルドエラーの確認
   # Dockerfile の構文エラー等
   ```

4. **メモリ不足**
   ```bash
   # ログで "Killed" や "OOMKilled" を確認
   # 無料プラン（512MB）では不足する場合がある

   # 解決策: 有料プランへアップグレード
   koyeb app update link-persona-bot --instance-type nano
   ```

### 問題2: スラッシュコマンドが表示されない

**症状:**
- `/persona` を入力しても候補が出ない

**原因と解決策:**

1. **Bot権限が不足**
   - Botの招待URLを再生成
   - `applications.commands` スコープを追加
   - Botを再招待

2. **コマンドの同期が完了していない**
   ```bash
   # Botログを確認
   koyeb app logs link-persona-bot | grep "Logged in as"

   # 期待されるログ:
   # Logged in as Link Persona Bot (ID: 123456789012345678)
   # Available personas: sarcastic
   ```

3. **Discordアプリを再起動**
   - Discord アプリを完全に終了
   - 再起動してコマンドをリフレッシュ

### 問題3: LLM APIエラー

**症状:**
- Botが応答するが、エラーメッセージが返る
- "エラーが発生しました: ..." と表示

**原因と解決策:**

1. **APIキーが無効**
   ```bash
   # ローカルでテスト
   uv run python tools/test/test_llm_connection.py

   # Koyeb環境変数を確認
   koyeb secrets get llm-api-key

   # 再設定
   koyeb secrets update llm-api-key --value "NEW_KEY"
   ```

2. **API URLが間違っている**
   ```bash
   # 正しいURLを確認
   # Qwen: https://dashscope.aliyuncs.com/compatible-mode/v1
   # OpenAI: https://api.openai.com/v1
   # OpenRouter: https://openrouter.ai/api/v1

   # 環境変数を修正
   koyeb app update link-persona-bot \
     --env LLM_API_URL=https://correct-url.com/v1
   ```

3. **モデル名が間違っている**
   ```bash
   # 利用可能なモデルを確認
   # Qwen: qwen-turbo, qwen-plus, qwen-max
   # OpenAI: gpt-3.5-turbo, gpt-4

   # 環境変数を修正
   koyeb app update link-persona-bot \
     --env LLM_MODEL=qwen-plus
   ```

4. **クレジット不足（OpenRouter）**
   - OpenRouterダッシュボードでクレジット残高を確認
   - https://openrouter.ai/credits
   - 追加チャージが必要

5. **レート制限**
   ```bash
   # ログでレート制限エラーを確認
   # "Rate limit exceeded" 等

   # 解決策:
   # - 別のモデルに変更
   # - 別のプロバイダーに切り替え
   # - レート制限の上限を引き上げ
   ```

### 問題4: ペルソナが読み込まれない

**症状:**
- `/persona` で "ペルソナが見つかりません" と表示

**原因と解決策:**

1. **YAMLファイルが存在しない**
   ```bash
   # リポジトリを確認
   ls api/personas/

   # 期待される出力:
   # sarcastic.yaml
   ```

2. **YAMLの構文エラー**
   ```bash
   # ローカルでYAMLを検証
   python -c "import yaml; yaml.safe_load(open('api/personas/sarcastic.yaml'))"

   # エラーがあれば修正
   ```

3. **Dockerイメージに含まれていない**
   ```bash
   # Dockerfile を確認
   # COPY api/ ./api/ が含まれているか確認

   # 再ビルド
   koyeb app redeploy link-persona-bot
   ```

### 問題5: メモリ不足でクラッシュ

**症状:**
- Botが定期的にオフラインになる
- ログに "OOMKilled" や "Killed"

**原因と解決策:**

1. **無料プラン（512MB）では不足**
   ```bash
   # メモリ使用量を確認
   koyeb app metrics link-persona-bot

   # 有料プランへアップグレード
   # Nano: $5.5/month (1GB RAM)
   koyeb app update link-persona-bot --instance-type nano
   ```

2. **会話履歴が大きくなりすぎ**
   - コードで履歴制限を設定（既に20件に制限済み）
   - 定期的にクリアする仕組みを追加

3. **依存関係の最適化**
   ```bash
   # 不要なパッケージを削除
   # pyproject.toml を見直す
   ```

### 問題6: デプロイが失敗する

**症状:**
- Koyebのビルドが "Failed" になる

**原因と解決策:**

1. **Dockerfileの構文エラー**
   ```bash
   # ローカルでビルドテスト
   docker build -t test .

   # エラーを修正
   ```

2. **依存関係のインストール失敗**
   ```bash
   # ログを確認
   koyeb app logs link-persona-bot --tail 200

   # pyproject.toml の依存関係を確認
   ```

3. **Pythonバージョンの不一致**
   ```bash
   # Dockerfile のPythonバージョンを確認
   # FROM python:3.12-slim

   # pyproject.toml の requires-python を確認
   # requires-python = ">=3.12"
   ```

---

## 6. 継続的デプロイ（CI/CD）

Koyebは自動的にGitHubリポジトリと連携し、mainブランチへのプッシュで自動デプロイします。

### 6.1 自動デプロイの流れ

1. **ローカルで開発**
   ```bash
   # 新しいブランチを作成
   git checkout -b feat/new-persona

   # コードを変更
   # 例: api/personas/professor.yaml を追加

   # コミット
   git add .
   git commit -m "feat: Add professor persona"

   # プッシュ
   git push origin feat/new-persona
   ```

2. **GitHubでPRを作成**
   - PRを作成
   - レビュー・テスト
   - mainにマージ

3. **Koyebが自動デプロイ**
   - mainへのマージを検知
   - Dockerイメージをビルド
   - 新しいインスタンスをデプロイ
   - ヘルスチェック成功後、トラフィックを切り替え
   - 古いインスタンスを停止

### 6.2 デプロイ履歴の確認

```bash
# Webコンソールで確認
# https://app.koyeb.com/apps/link-persona-bot/deployments

# CLIで確認
koyeb app deployments link-persona-bot
```

### 6.3 ロールバック

```bash
# 以前のデプロイメントIDを確認
koyeb app deployments link-persona-bot

# ロールバック
koyeb app rollback link-persona-bot --deployment-id <DEPLOYMENT_ID>
```

### 6.4 GitHub Actionsとの連携（オプション）

Koyebの自動デプロイに加えて、GitHub Actionsでテストを実行できます。

`.github/workflows/test.yml`:
```yaml
name: Test

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run linter
        run: uv run ruff check .

      - name: Run type checker
        run: uv run mypy .

      - name: Run tests
        run: uv run pytest
```

---

## 7. コスト管理

### 7.1 Koyeb コスト

**無料枠（Free）:**
```
✅ 512MB RAM
✅ 2GB Disk
✅ 100GB Transfer/month
✅ 常時起動可能
✅ 1アプリまで
```

**有料プラン:**
```
Nano: $5.50/month
- 1GB RAM
- 10GB Disk
- 250GB Transfer/month

Small: $11/month
- 2GB RAM
- 20GB Disk
- 500GB Transfer/month
```

**推奨プラン:**
- 無料枠で十分（Discord Bot + 軽量なLLM処理）
- メモリ不足の場合のみNanoへアップグレード

### 7.2 LLM API コスト

#### Qwen（Alibaba Cloud）

**無料枠:**
- 月100万トークン（約50万字）

**料金（2024年時点）:**
```
qwen-turbo: ¥0.002/1000トークン（入力）、¥0.006/1000トークン（出力）
qwen-plus:  ¥0.004/1000トークン（入力）、¥0.012/1000トークン（出力）
qwen-max:   ¥0.040/1000トークン（入力）、¥0.120/1000トークン（出力）
```

**月間コスト試算（qwen-plus、1000メッセージ）:**
```
1メッセージあたり:
- 入力: 200トークン（システムプロンプト + ユーザー入力）
- 出力: 100トークン（応答）

月間コスト:
= (200 × 1000 × ¥0.004 + 100 × 1000 × ¥0.012) / 1000
= (¥800 + ¥1200) / 1000
= ¥2 ≈ $0.013

実質無料（無料枠100万トークン以内）
```

#### OpenAI

**料金（2024年時点）:**
```
gpt-3.5-turbo: $0.0005/1000トークン（入力）、$0.0015/1000トークン（出力）
gpt-4:         $0.03/1000トークン（入力）、$0.06/1000トークン（出力）
gpt-4-turbo:   $0.01/1000トークン（入力）、$0.03/1000トークン（出力）
```

**月間コスト試算（gpt-3.5-turbo、1000メッセージ）:**
```
= (200 × 1000 × $0.0005 + 100 × 1000 × $0.0015) / 1000
= ($100 + $150) / 1000
= $0.25
```

#### OpenRouter

**料金:**
- プロバイダーのAPI料金 + OpenRouterマージン（通常10-20%）

**推奨モデル（コスト順）:**
```
1. meta-llama/llama-3-8b-instruct: ~$0.0002/1000トークン
2. google/gemini-pro: ~$0.0005/1000トークン
3. openai/gpt-3.5-turbo: ~$0.0006/1000トークン
4. anthropic/claude-3-haiku: ~$0.0008/1000トークン
5. qwen/qwen-2-72b-instruct: ~$0.0009/1000トークン
```

詳細: https://openrouter.ai/models

### 7.3 コスト最適化のヒント

1. **無料枠を活用**
   - Qwenの無料枠（月100万トークン）を最大限活用
   - 超過しそうになったらOpenRouterの安価なモデルへ切り替え

2. **システムプロンプトの最適化**
   - 簡潔なシステムプロンプトでトークン数を削減
   - 不要な例文を削除

3. **会話履歴の制限**
   - 現在20件に制限済み（最大10往復）
   - 必要に応じてさらに削減

4. **レート制限の実装**
   - ユーザーあたりのコマンド実行回数を制限
   - スパム対策にもなる

5. **モデルの使い分け**
   ```python
   # 簡単なタスク: qwen-turbo
   # 通常のタスク: qwen-plus（推奨）
   # 高品質が必要: qwen-max
   ```

6. **モニタリング**
   ```bash
   # Qwen ダッシュボードで使用量を確認
   # https://dashscope.console.aliyun.com/

   # OpenRouter ダッシュボード
   # https://openrouter.ai/usage
   ```

---

## 付録

### A. 環境変数一覧

| 変数名 | 説明 | 必須 | 例 |
|--------|------|------|-----|
| `DISCORD_TOKEN` | Discord Botトークン | ✅ | `MTAxMjM0NTY3ODkwMTIzNDU2Nw.GaBcDe.Fg...` |
| `LLM_PROVIDER` | LLMプロバイダー | ✅ | `qwen`, `openai`, `openrouter` |
| `LLM_API_KEY` | LLM APIキー | ✅ | `sk-xxxxxxxxxxxxxxxxxxxx` |
| `LLM_API_URL` | LLM APIエンドポイント | ❌ | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | 使用するモデル | ❌ | `qwen-plus`, `gpt-3.5-turbo` |
| `LLM_EXTRA_HEADER_HTTP_REFERER` | 追加ヘッダー（OpenRouter） | ❌ | `https://github.com/endo-ava/link-persona-bot` |
| `LLM_EXTRA_HEADER_X_TITLE` | 追加ヘッダー（OpenRouter） | ❌ | `Link Persona Bot` |
| `ENV` | 実行環境 | ❌ | `production`, `development` |

### B. 有用なリンク

- **Koyeb ダッシュボード**: https://app.koyeb.com/
- **Koyeb ドキュメント**: https://www.koyeb.com/docs
- **Discord Developer Portal**: https://discord.com/developers/applications
- **Discord.py ドキュメント**: https://discordpy.readthedocs.io/
- **Qwen Dashscope**: https://dashscope.console.aliyun.com/
- **OpenAI Platform**: https://platform.openai.com/
- **OpenRouter**: https://openrouter.ai/

### C. サポート

問題が解決しない場合は、以下をご確認ください:

1. **プロジェクトのissue**: https://github.com/endo-ava/link-persona-bot/issues
2. **Koyeb サポート**: https://www.koyeb.com/support
3. **Discord.py サポート**: https://discord.gg/discord-developers

---

**最終更新日**: 2025-11-02
