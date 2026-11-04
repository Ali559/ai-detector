.PHONY: help install dev build run test clean docker-build docker-run docker-stop

help:
	@echo "AI Deepfake Detection Service - Available Commands:"
	@echo ""
	@echo "  make install      Install dependencies"
	@echo "  make dev          Run development server"
	@echo "  make build        Build Docker image"
	@echo "  make run          Run Docker container"
	@echo "  make test         Run tests"
	@echo "  make clean        Clean up cache files"
	@echo "  make docker-build Build and start with docker-compose"
	@echo "  make docker-stop  Stop docker-compose services"
	@echo "  make logs         View docker-compose logs"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio httpx black isort flake8

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

build:
	docker build -t ai-service:latest .

run:
	docker run -p 8000:8000 --gpus all ai-service:latest

test:
	pytest tests/ -v --cov=app --cov-report=html

test-quick:
	pytest tests/ -v -x

format:
	black app/
	isort app/

lint:
	flake8 app/ --max-line-length=100
	black app/ --check

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker-compose up --build -d ai-service

docker-run:
	docker-compose up -d ai-service

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f ai-service

docker-clean:
	docker-compose down -v
	docker system prune -f

health:
	@curl -s http://localhost:8000/health | python -m json.tool

analyze-test:
	@echo "Testing analyze endpoint..."
	@curl -X POST http://localhost:8000/analyze \
		-F "file=@test_image.jpg" \
		| python -m json.tool