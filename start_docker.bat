@echo off
echo 🐳 Starting KOL Management System with Docker...
echo.
echo 📋 Port Configuration:
echo    - Frontend: http://localhost:3001
echo    - Backend API: http://localhost:8001
echo    - API Docs: http://localhost:8001/docs
echo    - PostgreSQL: localhost:5433
echo.
echo 🔐 Login Credentials:
echo    - Admin: admin@kolmanagement.com / Admin@123
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Stop any existing containers
echo 🛑 Stopping existing containers...
docker-compose down

REM Start services
echo 🚀 Starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check service status
echo.
echo 📊 Service Status:
docker-compose ps

echo.
echo 🎉 Setup complete!
echo.
echo 🌐 Open your browser:
echo    Frontend: http://localhost:3001
echo    API Docs: http://localhost:8001/docs
echo.
echo 📝 To view logs:
echo    docker-compose logs -f
echo.
echo 🛑 To stop:
echo    docker-compose down
echo.
pause