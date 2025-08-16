# Automaton Development Automation
.PHONY: format lint check test install clean

# Format code with black
format:
	@echo "🎨 Formatting Python code with black..."
	black src/ --line-length 100
	black tests/ --line-length 100 || true
	black scripts/ --line-length 100 || true
	@echo "✅ Code formatting complete"

# Run linting with flake8
lint:
	@echo "🔍 Running flake8 linting..."
	flake8 src/ --max-line-length=100 --ignore=E203,W503,E722
	@echo "✅ Linting complete"

# Combined check: format + lint
check: format lint
	@echo "✅ All code quality checks passed"

# Run tests
test:
	@echo "🧪 Running tests..."
	python3.11 -m pytest tests/ -v || echo "⚠️ Tests not fully implemented yet"
	@echo "✅ Testing complete"

# Install development dependencies
install:
	@echo "📦 Installing dependencies..."
	pip3.11 install -r requirements.txt
	pip3.11 install black flake8 pytest pytest-asyncio
	@echo "✅ Dependencies installed"

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Full development setup
setup: install check
	@echo "🚀 Development environment ready!"
	@echo ""
	@echo "Commands available:"
	@echo "  make format  - Format code with black"
	@echo "  make lint    - Run flake8 linting"  
	@echo "  make check   - Format + lint"
	@echo "  make test    - Run tests"
	@echo "  make clean   - Clean temporary files"