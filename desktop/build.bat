@echo off
REM ============================================================
REM  Gera o executavel do Mapa de Carga Horaria no Windows.
REM  Requisitos: Python 3.10+ instalado (com tkinter, que ja vem
REM  por padrao no instalador oficial do python.org).
REM  Resultado: dist\MapaCargaHoraria.exe
REM ============================================================
setlocal

echo [1/3] Instalando dependencias de build...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo [2/3] Gerando executavel com PyInstaller...
python -m PyInstaller --noconfirm mapa.spec
if errorlevel 1 goto erro

echo [3/3] Concluido!
echo Executavel gerado em: dist\MapaCargaHoraria.exe
goto fim

:erro
echo.
echo Ocorreu um erro durante o build. Verifique as mensagens acima.
exit /b 1

:fim
endlocal
