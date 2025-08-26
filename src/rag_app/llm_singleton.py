from langchain_ollama import ChatOllama

from rag_app.config import CONFIG


def get_llm():
    return ChatOllama(
        model=CONFIG.CHAT_MODEL,
        base_url=CONFIG.LLM_HOST
    )
