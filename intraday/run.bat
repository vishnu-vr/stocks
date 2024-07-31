@echo off
cd /d "%~dp0"
call .\bot\Scripts\activate

REM Define the list of inputs
set inputs=TORNTPOWER.NS

REM Loop through each input and run the Python script
for %%i in (%inputs%) do (
    start "" python .\macd_check_realtime.py %%i
)

pause
