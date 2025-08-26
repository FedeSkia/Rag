from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection

from rag_app.config import CONFIG


def create_postgres_checkpointer():
    db_conn = ("postgresql://" + CONFIG.DB_USER + ":" + CONFIG.DB_PWD + "@" + CONFIG.DB_HOST + ":"
               + CONFIG.DB_PORT.__str__() + "/postgres?sslmode=disable")
    conn = Connection.connect(db_conn, **{
        "autocommit": True,
        "prepare_threshold": 0,
    })
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer
