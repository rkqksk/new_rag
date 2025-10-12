.PHONY: help start stop

help:
	@echo "사용법:"
	@echo "  make start - Docker 서비스 시작"
	@echo "  make stop  - Docker 서비스 중지"

start:
	docker compose up -d

stop:
	docker compose down

status:
	docker compose ps
