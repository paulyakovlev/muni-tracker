1up:
	docker compose up -d --build

down:
	docker compose down

wipe:
	docker compose down -v

logs:
	docker compose logs -f fetcher
