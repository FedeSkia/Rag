from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection

from rag_app import config


def create_postgres_checkpointer():
    db_conn = ("postgresql://" + config.DB_USER + ":" + config.DB_PWD + "@" + config.DB_HOST + ":"
               + config.DB_PORT.__str__() + "/postgres?sslmode=disable")
    conn = Connection.connect(db_conn, **{
        "autocommit": True,
        "prepare_threshold": 0,
    })
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer
