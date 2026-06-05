#!/usr/bin/env bash

set -e

echo "🧹 Removing old venv if exists..."
rm -rf .venv

echo "🐍 Creating Python 3.12 virtual environment..."
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv

echo "⚡ Activating environment..."
source .venv/bin/activate

echo "📦 Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing dependencies..."
pip install \
    sqlalchemy \
    psycopg2-binary \
    fastmcp \
    mcp \
    python-dotenv \
    fastapi \
    uvicorn

echo "📌 Freezing requirements..."
pip freeze > requirements.txt

echo "✅ Environment ready!"

echo ""
echo "👉 Next step:"
echo "source .venv/bin/activate"
echo "python ./init/init_db.py"
echo "python ./init/seed_init_data.py"
echo "python mcp_server.py"