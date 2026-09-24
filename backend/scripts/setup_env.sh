#!/bin/bash

# Setup script for environment

echo "Setting up Naukri CRM HCP Module..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [[ $(echo "$python_version >= 3.11" | bc) -ne 1 ]]; then
    echo "Error: Python 3.11+ required. Found: $python_version"
    exit 1
fi

# Check Node.js version
node_version=$(node --version 2>&1 | grep -Po '\d+\.\d+\.\d+')
if [[ -z "$node_version" ]]; then
    echo "Error: Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "✓ Python 3.11+ found"
echo "✓ Node.js found"

# Backend setup
echo "Setting up backend..."
cd backend || exit
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
echo "✓ Backend setup complete"

# Frontend setup
echo "Setting up frontend..."
cd ../frontend || exit
npm install
cp .env.example .env
echo "✓ Frontend setup complete"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your configuration"
echo "2. Edit frontend/.env with your configuration"
echo "3. Run database migrations: cd backend && alembic upgrade head"
echo "4. Start backend: cd backend && uvicorn app.main:app --reload"
echo "5. Start frontend: cd frontend && npm run dev"
echo ""
echo "Application will be available at: http://localhost:5173"