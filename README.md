# How to build
cd docker/rag_app
docker compose build --no-cache
docker compose up

# Dev 
To work locally launch the docker-compose

# Test

to verify if the LLM reply use:
curl -N -X POST http://localhost:8000/invoke   -H "Content-Type: application/json"   -d '{"content": "hello"}' 
