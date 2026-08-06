@echo off
chcp 65001 > nul
echo ===================================================
echo  🚌 버스 배차 시간표 자동 생성기 로컬 실행 스크립트
echo ===================================================

echo.
echo [1/2] 백엔드 FastAPI 서버를 시작합니다... (Port: 8000)
start "Bus Backend" cmd /k "cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo [2/2] 프론트엔드 Vite 개발 서버를 시작합니다... (Port: 5173)
start "Bus Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo 실행 완료!
echo - 웹 브라우저에서 http://localhost:5173 으로 접속하세요.
echo - 백엔드 API 문서는 http://localhost:8000/docs 에서 확인 가능합니다.
echo ===================================================
pause
