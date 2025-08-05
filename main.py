from random import random
from langchain_core.runnables import RunnableConfig

from graph import create_graph

if __name__ == '__main__':
    config: RunnableConfig = {"configurable": {"thread_id": random()}}
    graph = create_graph()
    print(graph.invoke({"question": "What is it Tool use in the context of LLM?"}, config=config))
