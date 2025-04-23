IMAGE_NAME = chatgpt-db
SERVICE_NAME = jsonimport

build:
	docker-compose build

up:
	docker-compose up

import_json:
	docker-compose run --rm $(SERVICE_NAME) python import_json_files.py

import_conversation:
	docker-compose run --rm $(SERVICE_NAME) python import_conversation.py

allclean:
	docker-compose run --rm $(SERVICE_NAME) sh -c "rm -f /app/from_*.db"

run:
	docker-compose run --rm $(SERVICE_NAME) tail -f /dev/null

shell:
	docker-compose run --rm $(SERVICE_NAME) sh

logs:
	docker-compose logs -f

