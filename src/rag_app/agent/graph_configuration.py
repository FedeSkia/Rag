from __future__ import annotations

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from rag_app.ingestion.constants import USER_ID_KEY

""" Useful to store and retrieve information about a user using its id and the thread"""
CHECKPOINT_NS = "checkpoint_ns"

THREAD_ID = "thread_id"

class Configurable(TypedDict):
    thread_id: str
    user_id: str


class GraphRunnableConfig(TypedDict):
    configurable: Configurable


class GraphRunConfig(BaseModel):
    thread_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)

    def to_runnable(self) -> RunnableConfig:
        """ Transform the GraphRunConfig into a RunnableConfig """
        cfg: RunnableConfig = {
            "configurable": {
                THREAD_ID: self.thread_id,
                USER_ID_KEY: self.user_id,
                CHECKPOINT_NS: self.user_id,
            }
        }
        return cfg

    @classmethod
    def from_runnable(cls, runnable: RunnableConfig) -> GraphRunConfig:
        return GraphRunConfig(thread_id=runnable['configurable'][THREAD_ID], user_id=runnable['configurable'][USER_ID_KEY])

    @classmethod
    def from_headers(cls, *, thread_id: str, user_id: str) -> "GraphRunConfig":
        return cls(thread_id=thread_id, user_id=user_id)
