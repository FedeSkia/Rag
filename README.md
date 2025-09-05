#
Simple RAG Application.

# How to build
cd docker/rag_app
docker compose build --no-cache
docker compose up

# Dev 
To work locally launch the docker-compose
poetry run env APP_ENV=.env.local app

