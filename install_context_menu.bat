@echo off
REM Install context menu option for audio transcoding
REM Run this script as Administrator to add the context menu option

echo Installing Audio Transcoder context menu option...
echo.

REM Get the script directory
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%transcoder_menu.py

REM Find Python executable (use full path if available)
for /f "delims=" %%i in ('where python.exe 2^>nul') do set PYTHON_EXE=%%i
if not defined PYTHON_EXE (
    echo ERROR: Python not found in PATH!
    echo Please ensure Python is installed and added to your system PATH.
    pause
    exit /b 1
)
echo Using Python: %PYTHON_EXE%

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

REM Check if Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: transcoder_menu.py not found in script directory!
    pause
    exit /b 1
)

REM Add a single global registry entry under HKEY_CLASSES_ROOT\*
REM This ensures the menu item appears for any file selection, including
REM mixed-type selections (e.g. .mp3 + .flac together). The Python script
REM already skips non-audio files gracefully.
echo Adding context menu entry for all file types...

reg add "HKEY_CLASSES_ROOT\*\Shell\TranscodeToAIFF" /ve /d "Transcode to AIFF 48kHz" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\*\Shell\TranscodeToAIFF" /v "MultiSelectModel" /d "Player" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\*\Shell\TranscodeToAIFF\command" /ve /d "\"%PYTHON_EXE%\" \"%PYTHON_SCRIPT%\" \"%%1\"" /f >nul 2>&1

echo.
echo Context menu option installed successfully!
echo You can now right-click on audio files and select "Transcode to AIFF 48kHz"
echo This works for single files, multiple files, and mixed file type selections.
echo.
pause
