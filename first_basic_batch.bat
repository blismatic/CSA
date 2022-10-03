@echo off

:: ECHO Hello World! Your first batch file was printed on the screen successfully.
:: SET myVar=%cd%
:: ECHO %myVar%

set beginMsg=python main.py
set /p arguments=<args.txt
set c=%beginMsg% %arguments%
echo %c%

PAUSE