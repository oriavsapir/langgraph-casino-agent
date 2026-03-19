import uuid

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.api.dependencies import AppContext
from app.api.schemas import ChatRequest, ChatResponse, HealthResponse

router = APIRouter()

_ctx: AppContext | None = None


def init_routes(ctx: AppContext) -> None:
    """Inject the application context — called once at startup."""
    global _ctx
    _ctx = ctx


def _get_ctx() -> AppContext:
    if _ctx is None:
        raise RuntimeError("Application context not initialised")
    return _ctx


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    ctx = _get_ctx()
    return HealthResponse(
        status="ok",
        property=ctx.property_display_name,
        documents_loaded=ctx.store.document_count,
    )


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest) -> ChatResponse:
    ctx = _get_ctx()
    session_id = req.session_id or str(uuid.uuid4())

    config = {
        "configurable": {"thread_id": session_id},
    }

    try:
        result = await ctx.agent.ainvoke(
            {
                "messages": [HumanMessage(content=req.message)],
                "property_name": ctx.property_display_name,
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config=config,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc

    ai_messages = [
        m for m in result["messages"] if m.type == "ai"
    ]
    if not ai_messages:
        raise HTTPException(status_code=500, detail="Agent produced no response")

    reply = ai_messages[-1].content

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        property_name=ctx.property_display_name,
    )
