# syntax=docker/dockerfile:1

# Build stage
FROM python:3.12-slim AS builder

# uvインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# 依存関係をインストール（uvを使って直接pyproject.tomlから）
RUN uv pip install --system --no-cache .

# Runtime stage
FROM python:3.12-slim

# 作業ディレクトリ設定
WORKDIR /app

# builderステージから依存関係をコピー
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY api/ ./api/
COPY bot/ ./bot/

# 起動スクリプトをコピー
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# curlをインストール（ヘルスチェック用）
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# ポート公開
EXPOSE 8000

# ヘルスチェック（APIサーバーの稼働確認）
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーション起動
CMD ["/bin/bash", "/app/start.sh"]
