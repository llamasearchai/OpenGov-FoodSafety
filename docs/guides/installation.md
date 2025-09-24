# Installation

This guide will walk you through installing OpenGov-Food on your system.

## Prerequisites

Before installing OpenGov-Food, ensure you have the following:

- **Python 3.11 or higher** - The application requires Python 3.11+
- **pip** or **uv** - Package manager for Python dependencies
- **Git** - For cloning the repository

### Checking Python Version

```bash
python --version
# Should output: Python 3.11.x or higher
```

If you don't have Python 3.11+, download it from [python.org](https://python.org).

## Installation Methods

### Method 1: Install with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/llamasearchai/OpenGov-Food.git
cd OpenGov-Food

# Create virtual environment and install dependencies
uv venv
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Method 2: Install with pip

```bash
# Clone the repository
git clone https://github.com/llamasearchai/OpenGov-Food.git
cd OpenGov-Food

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Development Installation

If you plan to contribute to the project, install development dependencies:

```bash
# With uv
uv sync --extra dev

# With pip
pip install -e ".[dev]"
```

## Verification

After installation, verify everything is working:

```bash
# Check the installation
python -c "import opengovfood; print('OpenGov-Food installed successfully!')"

# Run the CLI help
opengov-food --help
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError` when importing opengovfood
**Solution**: Make sure you're in the virtual environment and have installed the package.

```bash
source .venv/bin/activate
pip install -e .
```

**Issue**: Python version too old
**Solution**: Upgrade to Python 3.11+.

```bash
# On macOS with Homebrew
brew install python@3.11

# On Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv
```

**Issue**: uv command not found
**Solution**: Install uv or use pip instead.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip method instead
```

## Next Steps

Once installed, proceed to the [Quick Start](quick-start.md) guide to get your first API running.