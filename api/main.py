from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional

from api.fetcher import get_article_fetcher, ArticleFetchError
from api.llm_client import get_llm_client
from api.persona_loader import get_persona_loader

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


# リクエスト・レスポンスモデル
class IngestRequest(BaseModel):
    """URL記事取り込みリクエスト"""
    url: HttpUrl
    user_id: Optional[str] = None
    guild_id: Optional[str] = None
    persona_id: Optional[str] = None  # 指定されたペルソナ（Noneの場合は自動選択）


class IngestResponse(BaseModel):
    """URL記事取り込みレスポンス"""
    url: str
    title: Optional[str]
    summary: str
    persona_id: str
    persona_name: str
    persona_icon: str
    persona_color: int
    truncated: bool


class DebateRequest(BaseModel):
    """ディベートモードリクエスト"""
    url: HttpUrl
    original_summary: Optional[str] = None  # 元の要約（省略可）


class DebateResponse(BaseModel):
    """ディベートモードレスポンス"""
    url: str
    original_stance: str  # 元の主張
    counter_argument: str  # 反論
    debate_summary: str  # ディベートのまとめ


@app.post("/ingest", response_model=IngestResponse)
async def ingest_url(request: IngestRequest):
    """
    URLから記事を取得し、ペルソナベースで要約を生成

    1. URLから記事本文を抽出
    2. LLMで記事のトーンと内容を分析
    3. 適切なペルソナを選択（または指定されたペルソナを使用）
    4. ペルソナの人格で要約を生成
    5. Discord Embed用の情報を返す
    """
    try:
        # 1. 記事を取得
        fetcher = get_article_fetcher()
        article = await fetcher.fetch_article(str(request.url))

        # 2. ペルソナを選択または取得
        persona_loader = get_persona_loader()

        if request.persona_id:
            # 指定されたペルソナを使用
            persona = persona_loader.get_persona(request.persona_id)
            if not persona:
                raise HTTPException(
                    status_code=400,
                    detail=f"Persona '{request.persona_id}' not found"
                )
        else:
            # デフォルトペルソナを使用（後で自動選択ロジックを追加可能）
            # とりあえず最初に見つかったペルソナを使用
            all_personas = persona_loader.get_all_personas()
            if not all_personas:
                raise HTTPException(
                    status_code=500,
                    detail="No personas available"
                )
            persona = next(iter(all_personas.values()))

        # 3. LLMで要約を生成
        llm_client = get_llm_client()

        # 要約生成プロンプト
        user_prompt = f"""
以下の記事を、あなたの人格で100字以内に要約してください。
記事タイトル: {article.get('title', '(タイトルなし)')}

記事本文:
{article['content']}

要約を生成してください（100字以内）:
"""

        summary = await llm_client.generate_persona_response(
            system_prompt=persona.get_system_message(),
            user_message=user_prompt,
        )

        return IngestResponse(
            url=article["url"],
            title=article.get("title"),
            summary=summary.strip(),
            persona_id=persona.id,
            persona_name=persona.name,
            persona_icon=persona.icon,
            persona_color=persona.color,
            truncated=article["truncated"],
        )

    except ArticleFetchError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch article: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) from e


@app.post("/debate", response_model=DebateResponse)
async def debate_article(request: DebateRequest):
    """
    記事の主張に対する反論を生成し、ディベート形式で返す

    1. URLから記事本文を抽出（または元の要約を使用）
    2. LLMで記事の主張を分析
    3. 反対の立場から反論を生成
    4. 両者の主張をまとめてディベート形式で返す
    """
    try:
        # 1. 記事を取得（元の要約がない場合）
        fetcher = get_article_fetcher()
        article = await fetcher.fetch_article(str(request.url))

        llm_client = get_llm_client()

        # 2. 元の主張を抽出
        if request.original_summary:
            original_stance = request.original_summary
        else:
            # 記事から主張を抽出
            stance_prompt = f"""
以下の記事の主な主張やメッセージを100字程度で要約してください。

記事タイトル: {article.get('title', '(タイトルなし)')}
記事本文:
{article['content']}

主張:
"""
            original_stance = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "あなたは記事の主張を客観的に分析する専門家です。"},
                    {"role": "user", "content": stance_prompt}
                ]
            )

        # 3. 反論を生成
        counter_prompt = f"""
以下の主張に対して、反対の立場から説得力のある反論を150字程度で生成してください。

元の主張:
{original_stance.strip()}

反論:
"""
        counter_argument = await llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "あなたは批判的思考を持つディベーターです。建設的な反論を生成してください。"},
                {"role": "user", "content": counter_prompt}
            ]
        )

        # 4. ディベートのまとめを生成
        debate_summary_prompt = f"""
以下の2つの主張について、簡潔なディベートのまとめを100字程度で生成してください。

【元の主張】
{original_stance.strip()}

【反論】
{counter_argument.strip()}

まとめ:
"""
        debate_summary = await llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "あなたは中立的な立場でディベートをまとめる司会者です。"},
                {"role": "user", "content": debate_summary_prompt}
            ]
        )

        return DebateResponse(
            url=article["url"],
            original_stance=original_stance.strip(),
            counter_argument=counter_argument.strip(),
            debate_summary=debate_summary.strip(),
        )

    except ArticleFetchError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch article: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
