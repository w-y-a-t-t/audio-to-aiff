@echo off
REM Uninstall context menu option for audio transcoding
REM Run this script as Administrator to remove the context menu option

echo Uninstalling Audio Transcoder context menu option...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

REM Remove registry entries
echo Removing context menu entries...

REM Remove the global entry (current install method)
reg delete "HKEY_CLASSES_ROOT\*\Shell\TranscodeToAIFF" /f >nul 2>&1

REM Remove legacy per-extension entries (from older installs)
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.mp3\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.wav\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.flac\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.m4a\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.aac\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.ogg\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.wma\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.aiff\Shell\TranscodeToAIFF" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.aif\Shell\TranscodeToAIFF" /f >nul 2>&1

echo.
echo Context menu option uninstalled successfully!
echo.
pause
