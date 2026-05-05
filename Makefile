.PHONY: db-dump down up logs trouble-sync

DUMP_FILE ?= backup_$(shell date +%Y%m%d_%H%M%S).sql

up:
	docker compose up -d --build

down:
	-docker compose stop ngrok
	docker compose down

logs:
	docker compose logs -f

db-dump:
	docker compose exec postgres pg_dump -U $${POSTGRES_USER:-trouble} $${POSTGRES_DB:-trouble} > $(DUMP_FILE)
	@echo "Dumped to $(DUMP_FILE)"

trouble-sync:
	curl -s -X POST -u ncbtrouble:ncb0190842 https://forecargo.ngrok.app/trouble/sync | python3 -m json.tool
