from langchain_ollama import ChatOllama

from src import config

def get_llm():
    return ChatOllama(
        model=config.CHAT_MODEL,
        base_url=config.LLM_HOST
    )
