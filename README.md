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
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MDY5OTdmZC1iZDAwLTQ2YTYtOGUxZS1mNDk2ODMzZTIzZWIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU3MDEyMzY2LCJpYXQiOjE3NTcwMDg3NjYsImVtYWlsIjoiZmVkZS5jb25vY2kud29ya0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiZmVkZS5jb25vY2kud29ya0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiI4MDY5OTdmZC1iZDAwLTQ2YTYtOGUxZS1mNDk2ODMzZTIzZWIifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1NzAwODc2Nn1dLCJzZXNzaW9uX2lkIjoiMWVlYzY1NjctM2E0MC00ZDYzLWEzZjktOTAyMzU1OGY0YmFhIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.IivCfUQOIA1b2zXFjD26iCylwyccIREvSl9MsO4M0LQ' \
  -d '{"content": "search for the word ISEE in my documents"}'