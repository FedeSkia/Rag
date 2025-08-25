# How to build
cd docker/rag_app
docker compose build --no-cache
docker compose up

# Dev 
To work locally launch the docker-compose

# Test

to verify if the LLM reply use:
curl -N -i -X POST http://localhost:8000/api/invoke \
  -H "Content-Type: application/json" \
  -H "x-thread-id": "ba40819f-5ccf-4070-9347-9b35ca5b3913" \
  -d '{"content": "my name is federico"}'
