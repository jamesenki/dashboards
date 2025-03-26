#!/bin/bash

# Local Code Quality Check Script for IoTSphere
# This script runs all code quality checks locally without requiring CI/CD

set -e  # Exit on error

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
  echo -e "\n${BLUE}=========================================================================${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}=========================================================================${NC}"
}

# Print section
print_section() {
  echo -e "\n${YELLOW}▶ $1${NC}"
}

# Print success
print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

# Print error
print_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Get the project root directory
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)")"
cd "$PROJECT_ROOT"

print_header "IoTSphere Code Quality Check"
echo "Running from directory: $PROJECT_ROOT"

# Check Python environment
print_section "Checking Python environment"
if ! command_exists python3; then
  print_error "Python 3 is not installed. Please install Python 3.9 or higher."
  exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Using $PYTHON_VERSION"

# Check Node.js environment
print_section "Checking Node.js environment"
if ! command_exists node; then
  print_error "Node.js is not installed. Please install Node.js 16 or higher."
  exit 1
fi

NODE_VERSION=$(node --version)
echo "Using Node.js $NODE_VERSION"
NPM_VERSION=$(npm --version)
echo "Using npm $NPM_VERSION"

# Check required Python packages
print_section "Checking Python packages"
MISSING_PYTHON_DEPS=false

check_py_dep() {
  if ! python3 -c "import $1" &>/dev/null; then
    print_error "$1 is not installed. Run: pip install $2"
    MISSING_PYTHON_DEPS=true
  else
    echo "✓ $1 found"
  fi
}

check_py_dep "black" "black"
check_py_dep "isort" "isort"
check_py_dep "flake8" "flake8"
check_py_dep "mypy" "mypy"
check_py_dep "pydocstyle" "pydocstyle"
check_py_dep "bandit" "bandit"

if [ "$MISSING_PYTHON_DEPS" = true ]; then
  echo -e "\nInstall all missing packages with:"
  echo "pip install black isort flake8 mypy pydocstyle bandit pre-commit"
  exit 1
fi

# Check required npm packages
print_section "Checking npm packages"
if [ ! -f "node_modules/.bin/eslint" ]; then
  print_error "npm packages are not installed. Run: npm install"
  exit 1
fi

# Run Python code quality checks
print_header "PYTHON CODE QUALITY CHECKS"

print_section "Checking Python code formatting with Black"
if black --check . 2>/dev/null; then
  print_success "Black check passed!"
else
  print_error "Black found formatting issues."
  echo "Run 'black .' to fix formatting issues."
  BLACK_FAILED=true
fi

print_section "Checking import sorting with isort"
if isort --check-only --profile black . 2>/dev/null; then
  print_success "isort check passed!"
else
  print_error "isort found import sorting issues."
  echo "Run 'isort --profile black .' to fix import sorting issues."
  ISORT_FAILED=true
fi

print_section "Checking PEP 8 compliance with flake8"
if flake8 . 2>/dev/null; then
  print_success "flake8 check passed!"
else
  print_error "flake8 found PEP 8 issues."
  FLAKE8_FAILED=true
fi

print_section "Checking type hints with mypy"
if [ -d "src" ]; then
  if mypy src 2>/dev/null; then
    print_success "mypy check passed!"
  else
    print_error "mypy found type hinting issues."
    MYPY_FAILED=true
  fi
else
  echo "src directory not found, skipping mypy checks."
fi

print_section "Checking docstrings with pydocstyle"
if [ -d "src" ]; then
  if pydocstyle --convention=google src 2>/dev/null; then
    print_success "pydocstyle check passed!"
  else
    print_error "pydocstyle found docstring issues."
    PYDOCSTYLE_FAILED=true
  fi
else
  echo "src directory not found, skipping pydocstyle checks."
fi

print_section "Running security checks with bandit"
if [ -d "src" ]; then
  if bandit -r src 2>/dev/null; then
    print_success "bandit check passed!"
  else
    print_error "bandit found security issues."
    BANDIT_FAILED=true
  fi
else
  echo "src directory not found, skipping bandit checks."
fi

# Run JavaScript code quality checks
print_header "JAVASCRIPT CODE QUALITY CHECKS"

print_section "Checking JavaScript code with ESLint"
if npm run lint:js 2>/dev/null; then
  print_success "ESLint check passed!"
else
  print_error "ESLint found issues."
  ESLINT_FAILED=true
fi

print_section "Checking CSS with stylelint"
if npm run lint:css 2>/dev/null; then
  print_success "stylelint check passed!"
else
  print_error "stylelint found issues."
  STYLELINT_FAILED=true
fi

print_section "Checking HTML with HTMLHint"
if npm run lint:html 2>/dev/null; then
  print_success "HTMLHint check passed!"
else
  print_error "HTMLHint found issues."
  HTMLHINT_FAILED=true
fi

print_section "Checking formatting with Prettier"
if npm run check-format 2>/dev/null; then
  print_success "Prettier check passed!"
else
  print_error "Prettier found formatting issues."
  echo "Run 'npm run format' to fix formatting issues."
  PRETTIER_FAILED=true
fi

# Summary
print_header "CODE QUALITY CHECK SUMMARY"

if [ "$BLACK_FAILED" = true ] || [ "$ISORT_FAILED" = true ] || [ "$FLAKE8_FAILED" = true ] || [ "$MYPY_FAILED" = true ] || [ "$PYDOCSTYLE_FAILED" = true ] || [ "$BANDIT_FAILED" = true ] || [ "$ESLINT_FAILED" = true ] || [ "$STYLELINT_FAILED" = true ] || [ "$HTMLHINT_FAILED" = true ] || [ "$PRETTIER_FAILED" = true ]; then
  print_error "Some checks failed. See above for details."
  
  echo -e "\nQuick fixes:"
  echo "1. Fix Python formatting: black ."
  echo "2. Fix import sorting: isort --profile black ."
  echo "3. Fix JavaScript formatting: npm run format"
  echo -e "\nOr run the comprehensive fixer: python tools/code-quality/check_code_quality.py --fix"
  
  exit 1
else
  print_success "All code quality checks passed!"
  exit 0
fi
