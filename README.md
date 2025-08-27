# How to build
cd docker/rag_app
docker compose build --no-cache
docker compose up

# Dev 
To work locally launch the docker-compose
poetry run env APP_ENV=.env.local app
# Test

to verify if the LLM reply use:
curl -N -i -X POST http://localhost:8000/api/invoke \
  -H "Content-Type: application/json" \
  -H "X-Thread-Id: 01" \
  -H "X-User-Id: 0" \
  -d '{"content": "my name is federico. search for the word Cliente in my documents"}'


to test the document upload:
curl --location 'http://localhost:8000/api/upload' \
--header 'x-user-id: 123' \
--form 'file=@"path-to-pdf"'