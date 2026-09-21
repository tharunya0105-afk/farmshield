@echo off
echo ========================================================
echo Starting FarmShield Autonomous AgTech System
echo ========================================================
cd backend
python -m uvicorn main:app --reload --port 8000 --host 127.0.0.1
pause
