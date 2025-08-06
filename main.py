

async def launch_graph(graph, input_message) -> str:
    for message_chunk, metadata in graph.stream(
            {"messages": input_message},
            stream_mode="messages",
    ):
        if message_chunk.content:
            yield message_chunk.content
