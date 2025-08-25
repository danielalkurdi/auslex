.PHONY: start start-backend build test test-e2e api-test docker-up

start:
	npm start

start-backend:
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

build:
	npm run build

test:
	npm test

test-e2e:
	npm run test:e2e

api-test:
	python tests/python/test_api_endpoints.py http://localhost:8000

docker-up:
	docker-compose up --build
