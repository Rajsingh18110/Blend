@echo off
echo ==============================================
echo        Starting Blend Search Server...
echo ==============================================

:: Add FFmpeg to PATH so music downloads work correctly
set PATH=%PATH%;C:\Users\Gaikwad\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin

:: Set required python environment variables
set PYTHONPATH=src
set PYTHONIOENCODING=utf-8

:: Start the daemon worker
python -m blend.cli --daemon-worker

pause
