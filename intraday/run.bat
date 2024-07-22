@echo off
cd /d "%~dp0"
call .\bot\Scripts\activate
python .\macd_check_realtime.py
pause
