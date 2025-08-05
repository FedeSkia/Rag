import asyncio
from random import random

from langchain_core.runnables import RunnableConfig

from graph import create_graph


def launch_graph(graph, input_message):
    for message_chunk, metadata in graph.stream(
            {"messages": input_message},
            stream_mode="messages",
    ):
        if message_chunk.content:
            print(message_chunk.content, "|", flush=True)


if __name__ == '__main__':
    config: RunnableConfig = {"configurable": {"thread_id": random()}}
    graph = create_graph()
    input_message = "What is Task Decomposition?"
    launch_graph(graph, input_message)
