@echo off

:: Start the virtual environment
.venv\Scripts\activate.bat

:: Run the script with the provided arguments
set /p arguments=<args.txt
python main.py %arguments%

PAUSE