.PHONY: help check fix install-deps clean

help:
	@echo "IoTSphere Code Quality Commands"
	@echo "------------------------------"
	@echo "make check        - Run all code quality checks"
	@echo "make fix          - Run automated fixes for code quality issues"
	@echo "make install-deps - Install all development dependencies"
	@echo "make clean        - Clean up temporary files"

check:
	@echo "Running code quality checks..."
	@./tools/code-quality/run_local_checks.sh

fix:
	@echo "Fixing code quality issues..."
	@python tools/code-quality/check_code_quality.py --fix

install-deps:
	@echo "Installing Python dependencies..."
	@pip install black isort flake8 mypy pydocstyle bandit pre-commit
	@echo "Installing npm dependencies..."
	@npm install

clean:
	@echo "Cleaning up temporary files..."
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "Clean complete!"
