# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

**Link Persona Bot** は、DiscordでURL共有された記事をAIが解析し、「人格（ペルソナ）」を持って要約するBotです。記事を独自のキャラクターボイスで擬人化し、単なる情報提供ではなくエンターテイメント体験を創出します。

### コアコンセプト
- **情報が「人格」になる**: 記事を独自のトーンと声を持つキャラクターに変換
- **遊び心重視**: ユーザーが試したくなるコマンド設計（例: `/debate`）
- **高い拡張性**: YAMLベースのペルソナテンプレートによる容易なカスタマイズ

## 開発コマンド

### セットアップ
```bash
# 依存関係のインストール（Python 3.12以上が必要）
uv sync

# 環境変数の設定
cp .env.example .env
```

### APIサーバーの起動
```bash
# 開発モード（ホットリロード有効）
uv run uvicorn api.main:app --reload

# 別の起動方法
uv run python -m api.main

# ヘルスチェック
curl http://localhost:8000/health
```

### Docker開発
```bash
# コンテナのビルドと起動
docker compose up -d

# ログの確認
docker compose logs -f api

# コンテナの停止
docker compose down
```

## アーキテクチャ

### システムコンポーネント

1. **Discord Bot** (`bot/` - 実装予定)
   - DiscordメッセージからURLを監視
   - FastAPIバックエンドへHTTPリクエストを送信
   - ペルソナベースの要約をDiscord Embedとして投稿

2. **FastAPIバックエンド** (`api/`)
   - Discord BotからのURL処理リクエストを受信
   - 記事抽出、解析、ペルソナ生成を統括
   - **現在の状態**: 基本的な`/health`エンドポイントのみ実装済み

3. **実装予定のモジュール**:
   - `api/fetcher.py`: `trafilatura`を使用した記事テキスト抽出
   - `api/qwen_client.py`: LLM操作用のQwen APIラッパー
   - `api/personas/`: YAMLベースのペルソナテンプレート（例: `sarcastic.yaml`, `anime.yaml`）
   - `context/memory.py`: ユーザー履歴用の軽量RAG（FAISSまたはインメモリ）

### リクエストフロー（計画中のアーキテクチャ）

```
ユーザーがDiscordにURLを投稿
  ↓
Discord BotがURLを検出
  ↓
POST /ingest {url, user_id, guild_id} → FastAPI
  ↓
1. 記事テキストの抽出（trafilatura）
2. トーンと著者ペルソナの分析（Qwen API）
3. マッチするペルソナテンプレートを選択（YAML）
4. ペルソナベースのナレーション生成（Qwen API）
  ↓
JSONレスポンスを返却 → Discord Bot
  ↓
Discord Embedで投稿（ペルソナの個性を反映）
```

## 重要な技術的決定事項

### パッケージ管理
- **uv**を使用（pip/poetryではない）
- Python 3.12以上が必須
- パッケージは`pyproject.toml`で定義、`[tool.hatch.build.targets.wheel]`で`api`パッケージを設定

### ペルソナテンプレートシステム
ペルソナは`api/personas/`内のYAMLファイルとして定義（未実装）:

```yaml
# 例: personas/sarcastic.yaml
name: "毒舌ジャーナリスト"
icon: "👁️"
color: 0xff4500
system_prompt: |
  あなたは皮肉たっぷりのベテランジャーナリストです。
  要約は100字以内で、必ず「…らしいですよ？」や「どうせ～」などの言い回しを使い、
  少し冷笑的に、でも核心を突いて話してください。
```

新しいペルソナの追加は、コード変更なしでYAMLファイルの追加・編集のみで完了すること。

### 非機能要件（docs/01.project.mdより）

- **パフォーマンス**: URL投稿からBot要約まで約10秒の応答時間を目標
- **記事抽出**: 静的HTMLサイトのみサポート（JSレンダリングが必要なSPAは対象外）
- **レート制限**: ユーザーあたり1分間に1コマンド
- **コスト制御**: LLMに送信前に記事テキストを最大2000文字に切り詰め
- **セキュリティ**: APIキーはKoyeb Secrets（環境変数）で管理、ハードコード禁止

## 機能ロードマップ

### 実装済み（MVPフェーズ）
- ✅ FastAPI基本構造
- ✅ `/health`ヘルスチェックエンドポイント
- ✅ Python 3.12を使用したDocker環境
- ✅ uv依存関係管理

### 優先機能（要件定義より）
- **F101 [Must]**: Auto Persona Summarize - URLを自動検出、記事抽出、ペルソナベース要約を生成
- **F201 [Must]**: Persona Chat Mode - `/persona <style>`コマンドでBotの人格を切り替えて会話継続
- **F302 [Must]**: Chat Memory - F201会話モード中の会話コンテキストを維持
- **F202 [Should]**: Debate Mode - `/debate`コマンドで反論を生成
- **F301 [Could]**: Context Memory (RAG) - ユーザーの過去のリンク履歴を記憶してパーソナライズコメント

## プロジェクトドキュメント

重要な設計ドキュメントは`docs/`配下にあります:
- `docs/01.project.md`: 機能優先度（MoSCoW）を含む完全な要件定義書
- `docs/02.architecture.md`: 技術アーキテクチャ、ワークフロー例、ペルソナテンプレート形式

新機能を実装する際は、プロジェクトビジョンとの整合性を確保するため、必ずこれらのドキュメントを参照してください。

## デプロイ先

- **ホスティング**: Koyeb（無料枠）
- **コンテナ**: マルチステージビルドのDocker
- **CI/CD**: GitHub Actionsによる自動デプロイ（予定）
- **データ永続化**: RAGデータはエフェメラル（再デプロイで消失）- 要件上これは許容される
