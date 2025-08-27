from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection

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
