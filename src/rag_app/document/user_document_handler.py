import logging
from datetime import datetime
from typing import List

import psycopg
from fastapi import HTTPException
from pydantic import BaseModel, Field
from starlette import status

from rag_app.config import CONFIG, get_postgres_connection_string


class UserDocument(BaseModel):
    file_name: str = Field(...)
    user_id: str = Field(...)
    document_id: str = Field(...)
    created_at: datetime | None = None


def list_user_documents(user_id: str) -> List[UserDocument]:
    """
    Return one record per uploaded document for this user.
    Assumes chunks were saved with metadata keys:
      - user_id
      - doc_id
      - file_name
      - ingested_at
    """
    sql = """
          SELECT e.cmetadata ->>'user_id' AS user_id, e.cmetadata->>'file_name' AS file_name, e.cmetadata->>'document_id' AS document_id, MIN (COALESCE ((e.cmetadata->>'ingested_at')::timestamptz, NOW())) AS created_at
          FROM langchain_pg_embedding e
              JOIN langchain_pg_collection c
          ON e.collection_id = c.uuid
          WHERE c.name = %s
            AND e.cmetadata->>'user_id' = %s
          GROUP BY 1, 2, 3
          ORDER BY created_at DESC;
          """
    with psycopg.connect(get_postgres_connection_string()) as conn, conn.cursor() as cur:
        try:
            cur.execute(sql, (CONFIG.DOCUMENTS_COLLECTION, user_id))
            rows: list[tuple] = cur.fetchall()
            if len(rows) == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return [
                UserDocument(user_id=row[0], file_name=row[1], document_id=row[2], created_at=row[3])
                for row in rows
            ]
        except HTTPException as e:
            raise e
        except Exception as e:
            logging.error(f"DB error: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DB error: {type(e).__name__}: {e}",
            )


def delete_user_document(user_id: str, document_id: str) -> int:
    """
    Delete all chunks of a document for a given user.
    Returns number of rows deleted.
    """
    sql = """
          DELETE
          FROM langchain_pg_embedding e USING langchain_pg_collection c
          WHERE e.collection_id = c.uuid
            AND c.name = %s
            AND e.cmetadata->>'user_id' = %s
            AND e.cmetadata->>'document_id' = %s; \
          """
    try:
        with psycopg.connect(get_postgres_connection_string()) as conn, conn.cursor() as cur:
            cur.execute(sql, (CONFIG.DOCUMENTS_COLLECTION, user_id, document_id))
            deleted = cur.rowcount
            conn.commit()
            if deleted == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return deleted
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error while deleting document {document_id} for user {user_id}: {e}",
        )
