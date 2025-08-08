import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER")
DB_PWD = os.getenv("DB_PWD")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS")
CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_HOST = os.getenv("LLM_HOST")

env_vars = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_USER": DB_USER,
    "DB_PWD": DB_PWD,
    "ALLOW_ORIGINS": ALLOW_ORIGINS,
    "CHAT_MODEL": CHAT_MODEL,
    "EMBEDDING_MODEL": EMBEDDING_MODEL,
    "LLM_HOST": LLM_HOST,
}

print("Loaded environment variables:")
for key, value in env_vars.items():
    print(f"{key:15} = {value}")
