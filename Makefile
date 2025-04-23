# Makefile
# --- Make targets ---
# make build              → docker-compose build
# make up                 → docker-compose up
# make import_json        → item_*.json → from_json_files.db
# make import_conversation→ conversation.json → from_conversation.db
# make allclean           → DB削除
# make run                → tail -f /dev/null (DBコンテナ維持)
# make runweb             → web.py 実行
# make shell              → sh に入る
# make logs               → docker logs

# Save as Makefile (same directory)

build:
	docker-compose build

up:
	docker-compose up

import_json:
	docker-compose run --rm jsonimport python import_json_files.py

import_conversation:
	docker-compose run --rm jsonimport python import_conversation.py

allclean:
	docker-compose run --rm jsonimport sh -c "rm -f /app/from_*.db"

run:
	docker-compose run --rm jsonimport tail -f /dev/null

runweb:
	docker-compose run --rm jsonimport python web.py

shell:
	docker-compose run --rm jsonimport sh

logs:
	docker-compose logs -f

