from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.services.openai_service import openai_service
from app.services.supabase_service import supabase

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    response = await openai_service.chat(request.message, request.context.model_dump())
    await supabase.insert(
        "chat_history",
        {
            "id": response.id,
            "user_id": request.user_id,
            "messages": [{"role": "user", "content": request.message}, {"role": "assistant", "content": response.text}],
            "context": request.context.model_dump(),
            "created_at": supabase.now(),
        },
    )
    return response


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    response = await chat(request)

    async def stream():
        yield response.model_dump_json()

    return StreamingResponse(stream(), media_type="application/json")
