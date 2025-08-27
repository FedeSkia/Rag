from typing import TypedDict, List, Annotated, Any, AsyncGenerator

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from rag_app.db_memory import create_postgres_checkpointer
from rag_app.graph_configuration import GraphRunConfig
from rag_app.ingestion.constants import USER_ID_KEY
from rag_app.llm_singleton import get_llm
from rag_app.retrieval.pdf_retriever import pdf_retriever


# Define state for application
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str


@tool("retrieve_documents", response_format="content_and_artifact")
def retrieve(query: str, user_id: str):
    """ Retrieves documents from a user's collection. Use this to answer user query """
    retrieved_documents: list[Document] = pdf_retriever.retriever(query=query, user_id=user_id)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_documents
    )
    return serialized, retrieved_documents


# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def query_or_respond(state: State, config: RunnableConfig):
    """Generate tool call for retrieval or respond."""
    chat_model = get_llm()
    llm_with_tools = chat_model.bind_tools([retrieve])
    input = [SystemMessage(content=f"User ID: {state.get(USER_ID_KEY)}")] + state["messages"]

    response = llm_with_tools.invoke(input)
    # MessagesState appends messages to state instead of overwriting
    return {"messages": [response]}


# Step 3: Generate a response using the retrieved content.
def generate(state: State):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Format into prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        f"{docs_content}"
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
           or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    chat_model = get_llm()
    response = chat_model.invoke(prompt)
    return {"messages": [response]}


def create_graph() -> CompiledStateGraph:
    graph_builder = StateGraph(State)
    graph_builder.add_node(query_or_respond)
    tools = ToolNode([retrieve])
    graph_builder.add_node(tools)
    graph_builder.add_node(generate)

    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)

    return graph_builder.compile(checkpointer=create_postgres_checkpointer())


async def launch_graph(input_message: str, user_id: str, config: GraphRunConfig) -> AsyncGenerator[Any, Any]:
    initial_state: State = {
        "messages": [HumanMessage(content=input_message)],
        "user_id": user_id,
    }
    for message_chunk, metadata in graph.stream(
            input=initial_state,
            stream_mode="messages",
            config=config.to_runnable(),
    ):
        if message_chunk.content:
            yield message_chunk.content


graph = create_graph()
