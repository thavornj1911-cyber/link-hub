@echo off
chcp 65001 >nul
echo ========================================================
echo   LinkHub - เริ่มต้นการทำงาน Web App สำหรับเก็บลิ้งค์
echo ========================================================
echo.
echo กำลังเปิดเซิร์ฟเวอร์ที่ http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
