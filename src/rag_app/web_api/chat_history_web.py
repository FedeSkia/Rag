import logging
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from fastapi import Header
from fastapi.responses import StreamingResponse
from langgraph.store.base import SearchItem
from langgraph.types import StateSnapshot
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
from rag_app.agent.graph import launch_graph, GRAPH
from rag_app.agent.graph_configuration import GraphRunConfig, THREAD_ID

from fastapi import Depends, APIRouter

from rag_app.db_memory import STORE

logger = logging.getLogger(__name__)
from rag_app.web_api.jwt_resolver import JWTBearer

chat_router = APIRouter(prefix="/chat")


class ChatHistory(BaseModel):
    thread_id: str = Field(..., min_length=1)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)


@chat_router.get("/get_user_conversation_history")
async def get_user_conversation_history(user_id: str = Depends(JWTBearer())) -> List[ChatHistory]:
    chats: list[SearchItem] = STORE.search(("chat_history", user_id))
    if not chats:
        return []
    return [
        ChatHistory(thread_id=chat.value["config"][THREAD_ID], created_at=chat.created_at, updated_at=chat.updated_at)
        for chat
        in chats]


class ChatHistoryThread(BaseModel):
    type: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


@chat_router.get("/get_user_conversation_thread")
async def get_user_conversation_thread(
        user_id: str = Depends(JWTBearer()),
        x_thread_id: Optional[str] = Header(..., alias="X-Thread-Id"), ) -> List[ChatHistoryThread]:
    """ returns thread chat history for a certain user and thread """
    cfg = GraphRunConfig.from_headers(thread_id=x_thread_id, user_id=user_id)
    state: StateSnapshot = GRAPH.get_state(cfg.to_runnable())
    if state is None or not state.values:
        return []
    msgs = state.values.get("messages", [])
    return [ChatHistoryThread(type=getattr(m, "type", ""), content=getattr(m, "content", "")) for m in msgs]


class InputData(BaseModel):
    content: str


@chat_router.post("/invoke")
async def invoke(
        data: InputData,
        x_thread_id: Optional[str] = Header(None, alias="X-Thread-Id"),
        user_id: str = Depends(JWTBearer()),
):
    thread_id = x_thread_id or str(uuid4())  # generate per request if absent
    cfg = GraphRunConfig.from_headers(thread_id=thread_id, user_id=user_id)
    stream = launch_graph(input_message=data.content, config=cfg)

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id
        }
    )
