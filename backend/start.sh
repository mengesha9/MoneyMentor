#!/bin/bash

# Start script for Render deployment
# This script sets up the environment and starts the FastAPI application

echo "🚀 Starting MoneyMentor API on Render..."

# Set Python path to include the backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start the FastAPI application with uvicorn
echo "🌟 Starting uvicorn server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT
