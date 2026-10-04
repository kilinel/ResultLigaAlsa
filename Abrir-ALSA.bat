@echo off
setlocal
cd /d "%~dp0"
if not exist "resultado_app.py" goto incomplete
if not exist "assets\app.ico" goto incomplete
py -3 -c "import sys, tkinter; assert sys.version_info >= (3,12)" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys, tkinter; assert sys.version_info >= (3,12)" >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.12 ou mais recente com Tkinter nao foi encontrado.
echo Leia o arquivo COMECE-AQUI.txt para instalar pelo site oficial.
pause
exit /b 1
:use_py
if /i "%~1"=="--check" goto checked
py -3 "resultado_app.py"
goto finished
:use_python
if /i "%~1"=="--check" goto checked
python "resultado_app.py"
:finished
if errorlevel 1 (
  echo.
  echo O aplicativo encontrou um erro. Copie o texto acima para pedir ajuda.
  pause
  exit /b 1
)
exit /b 0
:incomplete
echo Extraia o ZIP inteiro antes de abrir. Mantenha a pasta assets junto do app.
pause
exit /b 1

:checked
echo OK: arquivos do app e Python com Tkinter encontrados.
exit /b 0
