# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

**Link Persona Bot** は、Discord で共有された URL 記事を AI が独自の「人格」で要約する Bot です。記事を個性的なキャラクター（毒舌記者、教授、アニメキャラなど）のボイスで擬人化し、エンターテイメント体験を提供します。

## 開発コマンド

```bash
# セットアップ（Python 3.12+ 必須）
uv sync
cp .env.example .env  # DISCORD_TOKEN, LLM_API_KEY, LLM_PROVIDER を設定

# API サーバー起動（開発モード）
uv run uvicorn api.main:app --reload

# Discord Bot 起動
uv run python -m bot.main

# 本番モード（API + Bot 同時起動）
bash start.sh

# Docker 開発
docker compose up -d
docker compose logs -f api

# 接続テスト
uv run python tools/test/test_llm_connection.py
uv run python tools/test/test_discord_connection.py
```

## アーキテクチャ

### コアコンポーネント

1. **Discord Bot** (`bot/main.py`)
   - `/persona <style>` コマンドでペルソナ切り替え ✅実装済
   - メンション応答でペルソナチャット対応 ✅実装済
   - チャンネル別のペルソナ設定と会話履歴を保持（最新 20 件）✅実装済

2. **FastAPI バックエンド** (`api/main.py`)
   - 現在: `/health` エンドポイントのみ実装
   - 計画: `/ingest` で URL 解析・ペルソナ生成

3. **LLM クライアント** (`api/llm_client.py`)
   - **OpenAI 互換の汎用クライアント**（複数プロバイダー対応）
   - 環境変数: `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_API_URL`, `LLM_MODEL`
   - 対応: Qwen（デフォルト）, OpenAI, OpenRouter, Azure OpenAI, カスタム
   - プロバイダー切り替えは環境変数変更のみで可能

4. **ペルソナシステム** (`api/persona_loader.py`)
   - `api/personas/*.yaml` から定義を読み込み
   - ペルソナ定義: name, icon, color, description, system_prompt, examples
   - **新規追加はYAMLファイル作成のみ（コード変更不要）**

### リクエストフロー（計画中）

```
Discord に URL 投稿
  ↓
Bot が URL 検出
  ↓
POST /ingest → FastAPI
  ↓
1. trafilatura で記事抽出
2. LLM でトーン・著者分析
3. 適合ペルソナ選択（YAML）
4. ペルソナベースの要約生成
  ↓
Discord Embed で投稿
```

### 実装状況

**完了:**
- FastAPI 基本構造、LLM クライアント、ペルソナローダー
- Discord Bot: `/persona` コマンド、メンション応答、会話履歴

**計画:**
- 記事抽出（`api/fetcher.py`）、URL 自動要約（F101）、`/debate` コマンド（F202）、RAG 履歴（F301）

## 技術的決定事項

### パッケージ管理
- **uv** 使用（pip/poetry 不使用）
- Python 3.12+ 必須
- `pyproject.toml` で `api` と `bot` パッケージを定義

### LLM プロバイダー設定
環境変数で全設定を制御（ハードコード不要）:

```bash
# Qwen（デフォルト）
LLM_PROVIDER=qwen
LLM_API_KEY=sk-xxx
LLM_MODEL=qwen-plus

# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4
```

### ペルソナテンプレート
`api/personas/*.yaml` で定義:

```yaml
name: "毒舌ジャーナリスト"
icon: "👁️"
color: 0xff4500
system_prompt: |
  あなたは皮肉たっぷりのベテランジャーナリストです。
  核心を突きつつも少し意地悪な物言いが特徴。
```

### デプロイ
- **プラットフォーム:** Koyeb（無料枠）
- **起動:** `start.sh` が API（バックグラウンド）+ Bot（フォアグラウンド）を統括
- **シークレット:** 環境変数で管理（Koyeb Secrets）
- **データ永続化:** RAG データは再デプロイで消失（要件上許容）

## 機能優先度（MoSCoW）

- **F101 [Must]**: URL 自動要約 - 記事検出、抽出、ペルソナ要約生成
- **F201 [Must]**: ペルソナチャットモード - `/persona <style>` で人格切り替え ✅**実装済**
- **F302 [Must]**: 会話記憶 - F201 中の会話コンテキスト維持 ✅**実装済**
- **F202 [Should]**: ディベートモード - `/debate` で反論生成
- **F301 [Could]**: ユーザー履歴 RAG - 過去リンクを記憶してパーソナライズ

## 非機能要件

- **パフォーマンス:** URL 投稿から要約まで約 10 秒目標
- **記事抽出:** 静的 HTML のみ対応（SPA/JS レンダリング非対応）
- **レート制限:** ユーザーあたり 1 分間に 1 コマンド
- **コスト制御:** 記事を最大 2000 文字に切り詰めて LLM 送信
- **セキュリティ:** API キーは環境変数のみ（ハードコード禁止）

## ドキュメント

詳細な設計は `docs/` 参照:
- `docs/01.project.md`: 完全な要件定義（MoSCoW 優先度）
- `docs/02.architecture.md`: 技術アーキテクチャ、ワークフロー例

新機能実装時は、プロジェクトビジョンとの整合性確保のためこれらを参照すること。
