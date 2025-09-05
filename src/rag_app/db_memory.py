from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from psycopg import Connection

from rag_app.agent.graph_configuration import GraphRunConfig
from rag_app.config import get_postgres_connection_string


def create_postgres_checkpointer():
    db_conn = get_postgres_connection_string()
    conn = Connection.connect(db_conn, **{
        "autocommit": True,
        "prepare_threshold": 0,
    })
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer


CHECKPOINTER = create_postgres_checkpointer()

def create_postgres_store():
    db_conn = get_postgres_connection_string()
    conn = Connection.connect(db_conn, **{
        "autocommit": True,
        "prepare_threshold": 0,
    })
    store = PostgresStore(conn)
    store.setup()
    return store


STORE = create_postgres_store()


def store_user_conversation_history(config: GraphRunConfig):
    """ stores the thread ids chat history using the user_id as a key"""
    serializable_state = {
        "config": config.model_dump()
    }
    STORE.put(namespace=("chat_history", config.user_id), key=config.thread_id, value=serializable_state)
