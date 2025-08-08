import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


def index_document(vector_store: PGVector):
    # Load and chunk contents of the blog
    loader = WebBaseLoader(
        web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    # Index chunks
    _ = vector_store.add_documents(documents=all_splits)


def create_vector_store() -> PGVector:
    embeddings = OllamaEmbeddings(
        model="qwen3:0.6b",
    )
    DB_CONN = "postgresql://" + config.DB_HOST + ":" + config.DB_PWD + "@" + config.DB_HOST + ":" + config.DB_PORT + "/postgres?sslmode=disable"
    return PGVector(
        embeddings=embeddings,
        collection_name="my_docs",
        connection=DB_CONN,
    )
