import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from rag_app.agent.agent_state import State
from rag_app.agent.graph_configuration import GraphRunConfig
from rag_app.db_memory import create_postgres_checkpointer, create_postgres_store, store_user_conversation_history
from rag_app.llm_singleton import get_llm
from rag_app.retrieval.pdf_retriever import pdf_retriever, DocumentFound

logger = logging.getLogger(__name__)


def add_messages(state: State, new_messages: list, config: RunnableConfig) -> State:
    interaction_id = GraphRunConfig.from_runnable(config).interaction_id
    enriched_messages = []
    for message in new_messages:
        # Ensure additional_kwargs exists
        if not hasattr(message, "additional_kwargs") or message.additional_kwargs is None:
            message.additional_kwargs = {}
        # Inject interaction_id
        message.additional_kwargs["interaction_id"] = interaction_id
        message.additional_kwargs["timestamp"] = datetime.now(timezone.utc).isoformat()
        enriched_messages.append(message)
    state["messages"].extend(enriched_messages)
    return state


@tool("retrieve_documents", response_format="content_and_artifact")
def retrieve(query: str, config: RunnableConfig):
    """ Retrieves documents from a user's collection. Use this to answer user query """
    config = GraphRunConfig.from_runnable(config)
    documents: list[DocumentFound] = pdf_retriever.retriever(query=query, user_id=config.user_id)
    return documents, documents


# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def query_or_respond(state: State, config: RunnableConfig):
    """Generate tool call for retrieval or respond."""
    chat_model = get_llm()
    llm_with_tools = chat_model.bind_tools([retrieve])

    response = llm_with_tools.invoke(state["messages"])
    state = add_messages(state, [response], config)
    store_user_conversation_history(config=GraphRunConfig.from_runnable(config))
    return {"messages": state["messages"]}


# Step 3: Generate a response using the retrieved content.
def generate(state: State, config: RunnableConfig):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_message = recent_tool_messages[::-1]

    # Format into prompt
    documents: DocumentFound = tool_message[0].artifact
    docs_as_json = [asdict(doc) for doc in documents]
    retrieved_documents_as_json_for_llm = json.dumps(docs_as_json)

    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. You can specify the page number and the document name."
        " Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        f"{retrieved_documents_as_json_for_llm}"
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
    state = add_messages(state, [response], config)
    return {"messages": state["messages"]}


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

    return graph_builder.compile(checkpointer=create_postgres_checkpointer(), store=create_postgres_store())


async def launch_graph(input_message: str, config: GraphRunConfig) -> AsyncGenerator[Any, Any]:
    initial_state: State = {
        "messages": [HumanMessage(content=input_message,
                                  additional_kwargs={"interaction_id": config.interaction_id,
                                                     "timestamp": datetime.now(timezone.utc).isoformat()}
                                  )],
    }
    # Debug history.
    for message_chunk, metadata in GRAPH.stream(
            input=initial_state,
            stream_mode="messages",
            config=config.to_runnable(),
    ):
        chunk_type = message_chunk.type
        if chunk_type == "AIMessageChunk" and message_chunk.content:
            yield message_chunk.content
        elif chunk_type == "tool":
            docs: list[DocumentFound] = message_chunk.artifact
            docs_as_json = [asdict(doc) for doc in docs]
            yield "TOOL_MSG:" + json.dumps(docs_as_json)


GRAPH = create_graph()
