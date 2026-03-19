from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=2000, description="User message text"
    )
    session_id: str | None = Field(
        None,
        description="Optional session ID for conversation continuity. "
        "If omitted, a new session is created.",
    )


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Agent response text")
    session_id: str = Field(..., description="Session ID for follow-up messages")
    property_name: str = Field(..., description="Property the agent is serving")


class HealthResponse(BaseModel):
    status: str = "ok"
    property: str
    documents_loaded: int
