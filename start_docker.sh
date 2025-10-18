#!/bin/bash

echo "🐳 Starting KOL Management System with Docker..."
echo ""
echo "📋 Port Configuration:"
echo "   - Frontend: http://localhost:3001"
echo "   - Backend API: http://localhost:8001"
echo "   - API Docs: http://localhost:8001/docs"
echo "   - PostgreSQL: localhost:5433"
echo ""
echo "🔐 Login Credentials:"
echo "   - Admin: admin@kolmanagement.com / Admin@123"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start services
echo "🚀 Starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🌐 Open your browser:"
echo "   Frontend: http://localhost:3001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"