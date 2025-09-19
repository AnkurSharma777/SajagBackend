#!/bin/bash

# Setup script for Disaster Alert System

echo "🚀 Setting up Disaster Alert System..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p templates static/css static/js

# Copy environment template
echo "⚙️ Setting up environment..."
cp .env.template .env
echo "✏️ Please edit .env file with your Firebase credentials"

# Initialize database
echo "🗄️ Initializing database..."
python -c "
from app import init_db
init_db()
print('Database initialized successfully!')
"

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your Firebase credentials"
echo "2. Download your Firebase service account key as 'serviceAccountKey.json'"
echo "3. Run: python app.py"
echo "4. Open: http://localhost:5000"
echo ""
echo "🧪 For API testing:"
echo "- Use Postman to test POST /send_alert"
echo "- Check the API docs modal in the dashboard"
