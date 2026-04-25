PYTHON ?= python
PIP ?= pip
NPM ?= npm

install:
	cd backend && $(PIP) install -r requirements.txt
	cd frontend && $(NPM) install

setup:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo ".env ready"
	@echo "Configure alerts in .env:"
	@echo "  FIREBASE_PROJECT_ID, FIREBASE_SERVICE_ACCOUNT"
	@echo "  CALLMEBOT_PHONE, CALLMEBOT_APIKEY"
	@echo "Then run: make dev"

dev:
	cd backend && $(PYTHON) -m uvicorn main:app --reload --port 8000 & \
	cd frontend && $(NPM) run dev
