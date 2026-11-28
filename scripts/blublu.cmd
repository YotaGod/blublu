@echo off
REM blublu CLI entrypoint wrapper for Windows CMD
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%blublu.py" %*
exit /b %ERRORLEVEL%
