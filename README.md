#
Simple RAG Application.
Exposes 2 endpoints.
One to upload documents and another one to search in the documents.

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
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyYjljOThkNi1jZDM4LTQxYTAtOWVkNi0wNDc1NDNjMDYwM2UiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU2OTgzMjU4LCJpYXQiOjE3NTY5Nzk2NTgsImVtYWlsIjoiZmVkZS5jb25vY2kud29ya0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiZmVkZS5jb25vY2kud29ya0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIyYjljOThkNi1jZDM4LTQxYTAtOWVkNi0wNDc1NDNjMDYwM2UifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1Njk3OTY1OH1dLCJzZXNzaW9uX2lkIjoiZTZkMjM3ODAtZWUyZS00NzcwLWEwYTAtMmIxNTkzZDFmZGJmIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.8qtlT0I6HlbeNWEkcLfhzvAwBKLOUsimj4qNOmPXXLw' \
  -d '{"content": "my name is federico. search for the word Cliente in my documents"}'


to test the document upload:
curl --location 'http://localhost:8000/api/upload' \
--header 'x-user-id: 123' \
--form 'file=@"path-to-pdf"'