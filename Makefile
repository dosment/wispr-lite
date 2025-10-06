# Makefile for Wispr-Lite

.PHONY: help dev run test lint clean install deb preload smoke

help:
	@echo "Wispr-Lite development targets:"
	@echo "  make dev       - Install development dependencies"
	@echo "  make run       - Run Wispr-Lite"
	@echo "  make test      - Run tests"
	@echo "  make smoke     - Run smoke test"
	@echo "  make lint      - Run linters"
	@echo "  make clean     - Clean build artifacts"
	@echo "  make install   - Install for current user"
	@echo "  make deb       - Build .deb package"
	@echo "  make preload   - Preload Whisper models"

dev:
	pip install -e ".[dev]"

run:
	python -m wispr_lite.main

test:
	pytest tests/ -v

lint:
	flake8 wispr_lite/
	mypy wispr_lite/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

install:
	bash scripts/install.sh

deb:
	dpkg-buildpackage -us -uc -b

preload:
	bash scripts/preload_models.sh

smoke:
	bash scripts/smoke_test.sh
