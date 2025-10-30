from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Link Persona Bot API",
    description="API for Discord Bot that analyzes URLs and generates persona-based summaries",
    version="0.1.0",
)

# CORS設定（Discord Bot連携用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント

    サービスの稼働状態を確認するためのエンドポイント
    """
    return {"status": "ok"}


@app.get("/")
async def root():
    """
    ルートエンドポイント

    API情報を返す
    """
    return {
        "message": "Link Persona Bot API",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
