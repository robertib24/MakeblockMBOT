#!/bin/bash

# Start script for mBot IoT Gateway

echo "🤖 Starting mBot IoT Gateway..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if requirements are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Installing requirements..."
    pip install -r requirements.txt
fi

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "✅ Starting Flask server..."
echo "🌐 Dashboard will be available at: http://localhost:5000"
echo "📊 API endpoints at: http://localhost:5000/api/*"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python app.py
