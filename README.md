# How to build
In the base folder you can build the images with:
cd ./docker/rag_app
docker build -f docker/rag_app/Dockerfile -t rag-app .
cd ./docker/ollama
docker build -f docker/ollama/Dockerfile -t rag-app .

# Dev 
To work locally launch the docker-compose

#Test

to verify if the LLM reply use:
curl -N -X POST http://localhost:8000/invoke   -H "Content-Type: application/json"   -d '{"content": "hello"}' 
