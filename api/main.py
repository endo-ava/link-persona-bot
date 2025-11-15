"""Link Persona Bot API

Discord Botが記事要約とディベートを行うためのAPIエンドポイントを提供します。
"""

import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from api.config import get_settings
from api.exceptions import (
    ArticleFetchError,
    LLMError,
    PersonaNotFoundError,
)
from api.fetcher import get_article_fetcher
from api.llm_client import get_llm_client
from api.models.responses import HealthResponse
from api.persona_loader import get_persona_loader
from api.services.article_service import ArticleService
from api.services.debate_service import DebateService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 設定読み込み
settings = get_settings()

# FastAPIアプリケーション初期化
app = FastAPI(
    title="Link Persona Bot API",
    description="API for Discord Bot that analyzes URLs and generates persona-based summaries",
    version=settings.api_version,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === サービスの依存性注入 ===

# グローバルサービスインスタンス
_article_service: Optional[ArticleService] = None
_debate_service: Optional[DebateService] = None


def get_article_service() -> ArticleService:
    """ArticleServiceのシングルトンインスタンスを取得

    FastAPIの依存性注入で使用されます。
    """
    global _article_service
    if _article_service is None:
        _article_service = ArticleService(
            article_fetcher=get_article_fetcher(),
            llm_client=get_llm_client(),
            persona_loader=get_persona_loader(),
        )
    return _article_service


def get_debate_service() -> DebateService:
    """DebateServiceのシングルトンインスタンスを取得

    FastAPIの依存性注入で使用されます。
    """
    global _debate_service
    if _debate_service is None:
        _debate_service = DebateService(
            article_fetcher=get_article_fetcher(),
            llm_client=get_llm_client(),
            persona_loader=get_persona_loader(),
        )
    return _debate_service


# === リクエスト・レスポンスモデル ===

class IngestRequest(BaseModel):
    """URL記事取り込みリクエスト"""
    url: HttpUrl
    user_id: Optional[str] = None
    guild_id: Optional[str] = None
    persona_id: Optional[str] = None


class DebateRequest(BaseModel):
    """ディベートモードリクエスト"""
    persona_id: str
    user_message: str
    conversation_history: list[dict[str, str]] = []


# === エンドポイント ===

@app.get("/")
async def root() -> dict[str, str]:
    """ルートエンドポイント

    API情報を返します。
    """
    return {
        "message": "Link Persona Bot API",
        "version": settings.api_version,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> HealthResponse:
    """ヘルスチェックエンドポイント

    サービスの稼働状態を確認します。
    """
    return HealthResponse(
        status="ok",
        version=settings.api_version
    )


@app.post("/ingest")
async def ingest_url(
    request: IngestRequest,
    article_service: ArticleService = Depends(get_article_service)
) -> dict:
    """URLから記事を取得し、ペルソナベースで要約を生成

    1. URLから記事本文を抽出
    2. 適切なペルソナを選択（または指定されたペルソナを使用）
    3. ペルソナの人格で要約を生成
    4. Discord Embed用の情報を返す

    Args:
        request: 記事取り込みリクエスト
        article_service: 記事要約サービス（依存性注入）

    Returns:
        要約レスポンス

    Raises:
        HTTPException: 処理失敗時
    """
    logger.info(
        "Received ingest request",
        extra={
            "url": str(request.url),
            "persona_id": request.persona_id,
            "user_id": request.user_id,
        }
    )

    try:
        result = await article_service.generate_summary(
            url=str(request.url),
            persona_id=request.persona_id,
            user_id=request.user_id,
            guild_id=request.guild_id,
        )
        logger.info("Ingest request completed successfully")
        return result

    except ArticleFetchError as e:
        logger.warning(
            "Article fetch failed",
            extra={"url": str(request.url), "error": str(e)}
        )
        raise HTTPException(
            status_code=400,
            detail=f"記事の取得に失敗しました: {e.message}"
        ) from e

    except PersonaNotFoundError as e:
        logger.warning(
            "Persona not found",
            extra={"persona_id": request.persona_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=404,
            detail=f"ペルソナが見つかりません: {e.message}"
        ) from e

    except LLMError as e:
        logger.error(
            "LLM generation failed",
            extra={"url": str(request.url), "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"要約の生成に失敗しました: {e.message}"
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error in ingest endpoint",
            extra={"url": str(request.url), "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="内部サーバーエラーが発生しました"
        ) from e


@app.post("/debate")
async def debate_article(
    request: DebateRequest,
    debate_service: DebateService = Depends(get_debate_service)
) -> dict:
    """ペルソナとの対話レスポンスを生成

    指定されたペルソナの人格で、ユーザーメッセージに対するレスポンスを生成します。
    会話履歴を考慮したコンテキストベースの応答を返します。

    Args:
        request: ディベートリクエスト
        debate_service: ディベートサービス（依存性注入）

    Returns:
        ディベートレスポンス

    Raises:
        HTTPException: 処理失敗時
    """
    logger.info(
        "Received debate request",
        extra={
            "persona_id": request.persona_id,
            "conversation_history_count": len(request.conversation_history),
        }
    )

    try:
        # 会話履歴にユーザーメッセージを追加
        full_history = request.conversation_history.copy()
        full_history.append({
            "role": "user",
            "content": request.user_message
        })

        result = await debate_service.generate_debate(
            url="",  # 会話モードでは不要
            persona_id=request.persona_id,
            conversation_history=full_history,
        )
        logger.info("Debate request completed successfully")
        return result

    except PersonaNotFoundError as e:
        logger.warning(
            "Persona not found",
            extra={"persona_id": request.persona_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=404,
            detail=f"ペルソナが見つかりません: {e.message}"
        ) from e

    except LLMError as e:
        logger.error(
            "LLM generation failed",
            extra={"persona_id": request.persona_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"レスポンスの生成に失敗しました: {e.message}"
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error in debate endpoint",
            extra={"persona_id": request.persona_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="内部サーバーエラーが発生しました"
        ) from e


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting API server",
        extra={"host": settings.api_host, "port": settings.api_port}
    )

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
