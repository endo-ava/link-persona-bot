# syntax=docker/dockerfile:1

# Build stage
FROM python:3.12-slim AS builder

# uvインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# 依存関係をインストール
RUN uv pip install --system -r pyproject.toml

# Runtime stage
FROM python:3.12-slim

# 作業ディレクトリ設定
WORKDIR /app

# builderステージから依存関係をコピー
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY api/ ./api/

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# アプリケーション起動
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
