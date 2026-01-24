# Makefile for Rural Connectivity Mapper Data Pipeline

.PHONY: help install data-build test clean

help:
	@echo "Rural Connectivity Mapper - Data Pipeline"
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make data-build   - Run the complete data pipeline"
	@echo "  make test         - Run all tests"
	@echo "  make test-quality - Run quality/confidence tests only"
	@echo "  make clean        - Clean generated data files"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

data-build:
	@echo "Running data pipeline..."
	python scripts/run_pipeline.py
	@echo "✅ Pipeline complete"

test:
	@echo "Running all tests..."
	pytest -v
	@echo "✅ Tests complete"

test-quality:
	@echo "Running quality/confidence tests..."
	pytest -v tests/test_quality_confidence.py
	@echo "✅ Quality tests complete"

clean:
	@echo "Cleaning generated data files..."
	rm -rf data/bronze/*
	rm -rf data/silver/*
	rm -rf data/gold/*
	@echo "✅ Data files cleaned"
