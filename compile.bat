@echo off
REM Activate the virtual environment
call .\.venv\Scripts\activate

REM Compile the Python script using Nuitka
SET PYTHON=.venv\Scripts\python.exe
SET NUITKA=.venv\Scripts\python.exe -m nuitka

REM Compiling script
%NUITKA% --standalone --onefile^
    --lto=auto^
    --follow-imports^
    --show-progress^
    --enable-plugin=tk-inter^
    --windows-icon-from-ico=./assets/favicon.ico^
    --output-filename=PANBA.exe^
    --company-name=NTTIndonesia^
    --product-name=PANBA^
    --file-version=0.5.0^
    --product-version=1.2.5^
    --include-data-dir=assets=assets^
    --output-dir=%OUTPUT_DIR%^
    --disable-console^
    app.py

echo Compilation finished.
pause