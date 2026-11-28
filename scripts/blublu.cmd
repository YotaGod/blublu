@echo off
REM Blublu CLI entrypoint wrapper for Windows CMD
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%codsblu.py" %*
exit /b %ERRORERRORLEVEL%