#!/bin/bash
# CIPHER Quick Start
# For local development/testing without full setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CIPHER_DIR="$(dirname "$SCRIPT_DIR")"

echo "CIPHER Quick Start"
echo "=================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required"
    exit 1
fi

# Create venv if needed
if [ ! -d "$CIPHER_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$CIPHER_DIR/venv"
fi

# Activate venv
source "$CIPHER_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q asyncpg aiohttp python-dotenv

# Check for .env
if [ ! -f "$CIPHER_DIR/.env" ]; then
    echo "Creating default .env file..."
    cat > "$CIPHER_DIR/.env" << 'EOF'
CIPHER_DB_HOST=localhost
CIPHER_DB_PORT=5432
CIPHER_DB_NAME=ldb
CIPHER_DB_USER=lframework
CIPHER_DB_PASSWORD=
CIPHER_BASE_PATH=/opt/cipher
CIPHER_EMAIL=cipher@example.com
EOF
    echo "Please edit $CIPHER_DIR/.env with your database credentials"
fi

# Create directories
mkdir -p "$CIPHER_DIR"/{mind,logs}

echo ""
echo "Setup complete! Run with:"
echo "  cd $CIPHER_DIR"
echo "  source venv/bin/activate"
echo "  python run.py --help"
echo ""
echo "Or run a quick test (no database needed):"
echo "  python -c \"from tools.hash_learning import compute_entropy; print(compute_entropy('Test text'))\""
