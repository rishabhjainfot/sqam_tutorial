@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project environment. This happens only once.
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto :error
    .venv\Scripts\python.exe -m pip install --upgrade pip
    if errorlevel 1 goto :error
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" run_project.py
if errorlevel 1 goto :error
goto :end

:error
echo.
echo The launcher could not start. Check that Python 3 is installed and internet access is available for first-time package setup.
pause

:end
endlocal
