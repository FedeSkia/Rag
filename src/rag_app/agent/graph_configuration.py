from __future__ import annotations

from typing import TypedDict, Optional
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from rag_app.ingestion.constants import USER_ID_KEY, INTERACTION_ID_KEY

THREAD_ID = "thread_id"


class GraphRunConfig(BaseModel):
    thread_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    interaction_id: str | None = Field(default=None)

    def to_runnable(self) -> RunnableConfig:
        """ Transform the GraphRunConfig into a RunnableConfig """
        cfg: RunnableConfig = {
            "configurable": {
                THREAD_ID: self.thread_id,
                USER_ID_KEY: self.user_id,
                INTERACTION_ID_KEY: self.interaction_id,
            }
        }
        return cfg

    @classmethod
    def from_runnable(cls, runnable: RunnableConfig) -> GraphRunConfig:
        return GraphRunConfig(thread_id=runnable['configurable'][THREAD_ID], user_id=runnable['configurable'][USER_ID_KEY], interaction_id=runnable['configurable'][INTERACTION_ID_KEY])

    @classmethod
    def from_headers(cls, *, thread_id: str, user_id: str, interaction_id: str | None = None) -> "GraphRunConfig":
        return cls(thread_id=thread_id, user_id=user_id, interaction_id=interaction_id)
