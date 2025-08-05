from random import random
from langchain_core.runnables import RunnableConfig

from graph import create_graph

if __name__ == '__main__':
    config: RunnableConfig = {"configurable": {"thread_id": random()}}
    graph = create_graph()
    input_message = "What is Task Decomposition?"

    for step in graph.stream(
            {"messages": [{"role": "user", "content": input_message}]},
            stream_mode="values",
    ):
        print(step)

