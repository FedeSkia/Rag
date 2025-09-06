import logging
import logging.config
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware

from rag_app.config import CONFIG

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get("-")
        record.user_id = user_id_ctx.get("-")
        return True


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(rid)
        # If you decode JWT elsewhere, set user_id_ctx there
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


def setup_logging():
    level = CONFIG.LEVEL.upper()
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(exc_info)s",
            },
        },
        "filters": {
            "ctx": {"()": "rag_app.logging_setup.ContextFilter"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["ctx"],
            },
        },
        "root": {"level": level, "handlers": ["console"]},
        "loggers": {
            # LangChain / LangGraph / Ollama
            "langchain": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "langchain_core": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "langchain_community": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "langgraph": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "langchain_ollama": {"level": "INFO", "handlers": ["console"], "propagate": False},

            # your app
            "rag_app": {"level": level, "handlers": ["console"], "propagate": False},
        },
    }
    logging.config.dictConfig(LOGGING)


UVICORN_LOG = {
    "version": 1,
    "force": True,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(exc_info)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "uvicorn": {"level": "INFO", "propagate": True},
        "uvicorn.error": {"level": "INFO", "propagate": True},
        "uvicorn.access": {"level": "INFO", "propagate": True}
    }
}
