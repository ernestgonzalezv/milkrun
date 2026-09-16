# Atajos del dia a dia. `make` sin argumentos lista lo que hay.
.DEFAULT_GOAL := help
BACKEND := backend
PY := $(BACKEND)/.venv/bin/python
PIP := $(BACKEND)/.venv/bin/pip

.PHONY: help setup migrate seed run test lint fix bench schema web android clean

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup:  ## Crea el entorno virtual e instala dependencias
	python3 -m venv $(BACKEND)/.venv
	$(PIP) install --upgrade pip
	$(PIP) install -r $(BACKEND)/requirements.txt
	cd web && npm install

migrate:  ## Aplica las migraciones
	cd $(BACKEND) && .venv/bin/python manage.py migrate

seed:  ## Datos de ejemplo. CITY=nyc|chicago|la|havana STOPS=80
	cd $(BACKEND) && .venv/bin/python manage.py seed_demo \
		--city $(or $(CITY),nyc) --stops $(or $(STOPS),80) --reset --plan

seed-all:  ## Siembra las cuatro ciudades, para ver el selector de depositos lleno
	@for c in nyc chicago la havana; do \
		cd $(BACKEND) && .venv/bin/python manage.py seed_demo --city $$c --stops 80 --reset --plan; \
	done

run:  ## Levanta la API en el puerto 8000
	cd $(BACKEND) && .venv/bin/python manage.py runserver 8000

web:  ## Levanta el dashboard en el puerto 5173
	cd web && npm run dev

test:  ## Corre los tests del backend y del frontend
	cd $(BACKEND) && .venv/bin/python -m pytest
	cd web && npm run test -- --run

coverage:  ## Tests con cobertura y umbrales, igual que en CI
	cd $(BACKEND) && .venv/bin/python -m pytest -q --cov --cov-report=term
	cd web && npm run test:coverage

lint:  ## Revisa estilo y tipos
	cd $(BACKEND) && .venv/bin/ruff check .
	cd web && npm run lint && npx tsc --noEmit

fix:  ## Arregla lo que se pueda arreglar solo
	cd $(BACKEND) && .venv/bin/ruff check . --fix && .venv/bin/ruff format .

bench:  ## Compara el optimizador contra los baselines
	cd $(BACKEND) && .venv/bin/python -m optimizer.benchmark

bench-ref:  ## Anade la comparacion contra OR-Tools (lenta, requiere requirements-dev)
	cd $(BACKEND) && .venv/bin/python -m optimizer.benchmark --referencia

schema:  ## Genera el esquema OpenAPI en docs/openapi.yml
	cd $(BACKEND) && .venv/bin/python manage.py spectacular --file ../docs/openapi.yml

android:  ## Tests, analisis estatico, formato y APK de depuracion
	cd android && ./gradlew testDebugUnitTest detekt spotlessCheck lintDebug assembleDebug

clean:  ## Borra artefactos de build y caches
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.ruff_cache web/dist android/app/build
