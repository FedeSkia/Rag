import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import Header, Request
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.base import CheckpointTuple
from langgraph.store.base import SearchItem
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from rag_app.agent.graph import launch_graph
from rag_app.agent.graph_configuration import GraphRunConfig
from rag_app.web_api.jwt_resolver import get_user_id

from fastapi import Depends, APIRouter

from rag_app.db_memory import STORE, CHECKPOINTER

logger = logging.getLogger(__name__)
from rag_app.web_api.jwt_resolver import JWTBearer

chat_router = APIRouter(prefix="/chat")


class ChatHistory(BaseModel):
    thread_id: str
    created_at: datetime
    updated_at: datetime


class ChatHistoryWebResponse(BaseModel):
    chats: list[ChatHistory]


@chat_router.get("/get_user_conversation_history")
async def get_user_conversation_history(
        request: Request,
        _token: str = Depends(JWTBearer())):
    # chats: Item = STORE.get(namespace=("chat_history", get_user_id(request)))
    chats: list[SearchItem] = STORE.search(("chat_history", get_user_id(request)))

    chat_histories = []
    for chat in chats:
        config = chat.value["config"]
        chat_histories.append(
            ChatHistory(thread_id=config["thread_id"], created_at=chat.created_at, updated_at=chat.updated_at))

    return ChatHistoryWebResponse(chats=chat_histories)


@chat_router.get("/get_user_conversation_thread")
async def get_user_conversation_history(
        request: Request,
        _token: str = Depends(JWTBearer()),
        x_thread_id: Optional[str] = Header(..., alias="X-Thread-Id"), ):
    cfg = GraphRunConfig.from_headers(thread_id=x_thread_id, user_id=get_user_id(request))
    checkpoints: CheckpointTuple = list(CHECKPOINTER.list(config=cfg.to_runnable()))

    return []


class InputData(BaseModel):
    content: str


@chat_router.post("/invoke")
async def invoke(
        data: InputData,
        request: Request,
        x_thread_id: Optional[str] = Header(..., alias="X-Thread-Id"),
        _token: str = Depends(JWTBearer()),
):
    user_id = get_user_id(request)
    thread_id = x_thread_id or str(uuid4())  # generate per request if absent
    cfg = GraphRunConfig.from_headers(thread_id=thread_id, user_id=user_id)
    stream = launch_graph(input_message=data.content, config=cfg)

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id,
            "X-User-Id": str(uuid4()),
        }
    )
