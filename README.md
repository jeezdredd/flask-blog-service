# Microblog API

## Run
```bash 
cp .env.example .env
docker-compose up -d --build
```

API: http://localhost:8000/docs
Use header `api-key: test` (или alice/bob)

## Endpoints
### POST /api/medias
### POST /api/tweets
### DELETE /api/tweets/{id}
### GET /api/users/me
### GET /api/users/{id}