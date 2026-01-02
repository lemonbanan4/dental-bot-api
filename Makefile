PY?=python

.PHONY: build up push test lint

build:
	docker build -t lemonbanan4/dental-bot-api:latest .

up:
	docker-compose up --build

push: build
	docker push lemonbanan4/dental-bot-api:latest

test:
	$(PY) -m pytest -q

format:
	black . || true
