from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

import config
from graph import graph
from graph import launch_graph

app = FastAPI()
# initilizing our application
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.ALLOW_ORIGINS],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class InputData(BaseModel):
    content: str


@app.post("/api/invoke")
async def invoke(
        data: InputData,
        x_thread_id: Optional[str] = Header(default=None),  # client may send it, else create one
):
    thread_id = x_thread_id or str(uuid4())  # generate per request if absent
    cfg: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    stream = launch_graph(graph, data.content, config=cfg)

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id
        }
    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
