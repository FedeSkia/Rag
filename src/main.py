from random import random

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
import config
from graph import create_graph
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

config: RunnableConfig = {"configurable": {"thread_id": random()}}
graph = create_graph()


class InputData(BaseModel):
    content: str


@app.post("/invoke")
async def invoke(data: InputData):
    return StreamingResponse(
        launch_graph(graph, data.content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
