#!/bin/bash

echo "🚀 Starting Notary DApp Backend..."

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with required variables"
    exit 1
fi

# Run Flask app
python app.py