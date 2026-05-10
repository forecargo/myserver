.PHONY: db-dump db-restore down up logs trouble-sync

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

db-restore:
	@test -f "$(DUMP_FILE)" || { \
		echo "Usage: make db-restore DUMP_FILE=<path-to-backup.sql>"; \
		echo "Error: dump file '$(DUMP_FILE)' not found"; exit 1; \
	}
	@echo "WARNING: This will DROP and RECREATE database '$${POSTGRES_DB:-trouble}' on the running postgres container."
	@echo "         All existing data will be permanently lost."
	@echo "         Source dump: $(DUMP_FILE)"
	@printf "Type 'yes' to continue: "; read confirm; [ "$$confirm" = "yes" ] || { echo "Aborted."; exit 1; }
	docker compose up -d --wait postgres
	-docker compose stop trouble-api
	docker compose exec -T postgres psql -U $${POSTGRES_USER:-trouble} -d postgres -c \
		"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$${POSTGRES_DB:-trouble}' AND pid <> pg_backend_pid();" > /dev/null
	docker compose exec -T postgres dropdb -U $${POSTGRES_USER:-trouble} --if-exists $${POSTGRES_DB:-trouble}
	docker compose exec -T postgres createdb -U $${POSTGRES_USER:-trouble} $${POSTGRES_DB:-trouble}
	docker compose exec -T postgres psql -U $${POSTGRES_USER:-trouble} -d $${POSTGRES_DB:-trouble} -v ON_ERROR_STOP=1 < $(DUMP_FILE)
	-docker compose start trouble-api
	@echo "Restored from $(DUMP_FILE)"

trouble-sync:
	curl -s -X POST -u ncbtrouble:ncb0190842 https://forecargo.ngrok.app/trouble/sync | python3 -m json.tool
