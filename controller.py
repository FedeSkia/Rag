from random import random

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from graph import create_graph
from main import launch_graph

app = FastAPI()


class InputData(BaseModel):
    content: str


if __name__ == '__main__':
    # initilizing our application
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Your frontend URL
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    config: RunnableConfig = {"configurable": {"thread_id": random()}}
    graph = create_graph()


    # curl -N -X POST http://localhost:8000/invoke \
    #   -H "Content-Type: application/json" \
    #   -d '{"content": "hello"}'
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


    uvicorn.run(app, host="0.0.0.0", port=8000)
