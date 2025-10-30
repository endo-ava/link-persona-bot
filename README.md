# Link Persona Bot

Discord BotでURL共有された記事をAI解析し、ペルソナ別に要約するシステム

## 概要

このプロジェクトは、DiscordでURLが共有された際に自動で記事を取得・解析し、指定されたペルソナ（口調・キャラクター）で要約を生成するBotです。

## 技術スタック

- **Python**: 3.12+
- **パッケージ管理**: uv
- **API Framework**: FastAPI
- **Discord Bot**: discord.py (予定)
- **AI/LLM**: Qwen API (予定)
- **Web Scraping**: trafilatura (予定)
- **Containerization**: Docker

## セットアップ

### 前提条件

- Python 3.12以上
- uv（パッケージマネージャー）
- Docker & Docker Compose（オプション）

### uvのインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### ローカル開発環境のセットアップ

1. リポジトリのクローン

```bash
git clone <repository-url>
cd link-persona-bot
```

2. 依存関係のインストール

```bash
uv sync
```

3. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な環境変数を設定
```

4. APIサーバーの起動

```bash
# 開発モード（ホットリロード有効）
uv run uvicorn api.main:app --reload

# または
uv run python -m api.main
```

5. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# レスポンス例
# {"status":"ok"}

# API ドキュメント（Swagger UI）
# ブラウザで http://localhost:8000/docs にアクセス
```

### Dockerを使用したセットアップ

1. Dockerコンテナのビルドと起動

```bash
docker compose up -d
```

2. ログの確認

```bash
docker compose logs -f api
```

3. 動作確認

```bash
curl http://localhost:8000/health
```

4. コンテナの停止

```bash
docker compose down
```

## プロジェクト構造

```
link-persona-bot/
├── api/                    # FastAPI アプリケーション
│   └── main.py            # メインAPI（/health エンドポイント）
├── docs/                   # プロジェクトドキュメント
│   ├── 01.project.md      # 要件定義書
│   └── 02.architecture.md # アーキテクチャ設計書
├── pyproject.toml         # プロジェクト設定・依存関係
├── Dockerfile             # Dockerコンテナ定義
├── docker-compose.yml     # Docker Compose設定
├── .env.example           # 環境変数テンプレート
├── .gitignore             # Git除外設定
└── README.md              # このファイル
```

## 開発状況

### 実装済み

- ✅ FastAPI基本構造
- ✅ `/health` ヘルスチェックエンドポイント
- ✅ Docker環境
- ✅ uv依存関係管理

### 今後の実装予定

- ⬜ Discord Bot実装（discord.py）
- ⬜ URL抽出・記事取得機能（trafilatura）
- ⬜ Qwen API連携
- ⬜ ペルソナテンプレートシステム
- ⬜ RAG機能（ユーザーコンテキスト記憶）
- ⬜ `/persona` コマンド実装
- ⬜ `/debate` コマンド実装

## API エンドポイント

### `GET /health`

サーバーのヘルスチェック

**レスポンス例:**

```json
{
  "status": "ok"
}
```

### `GET /`

API情報の取得

**レスポンス例:**

```json
{
  "message": "Link Persona Bot API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

## ライセンス

TBD

## コントリビューション

TBD
