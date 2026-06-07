@echo off
REM Simple batch file to start the audio transcoder
REM Edit the WATCH_FOLDER path below to your desired folder

set WATCH_FOLDER=C:\Users\YourUsername\Music\ToTranscode
set PYTHON_SCRIPT=%~dp0transcoder_watch.py

echo Starting Audio Transcoder...
echo Watching folder: %WATCH_FOLDER%
echo.
echo Press Ctrl+C to stop
echo.

python "%PYTHON_SCRIPT%" "%WATCH_FOLDER%"

pause
