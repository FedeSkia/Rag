from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


# Define state for application
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
