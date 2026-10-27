@echo off
rem Gera dist\Retalhos\ (app), dist\Update.exe e o instalador dist\instalador\Retalhos_Setup_<versao>.exe
rem Uso: ferramentas\gerar_instalador.bat   (na raiz do projeto ou com duplo clique)
setlocal
cd /d "%~dp0.."

set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
    echo Inno Setup 6 nao encontrado. Instale com: winget install JRSoftware.InnoSetup
    exit /b 1
)

for /f %%v in ('%PY% -c "import retalhos; print(retalhos.__version__)"') do set VERSAO=%%v
echo === Retalhos %VERSAO% ===

%PY% -m PyInstaller --noconfirm Retalhos.spec || exit /b 1
%PY% -m PyInstaller --noconfirm Update.spec || exit /b 1
"%ISCC%" /Q /DAppVersion=%VERSAO% instalador\Retalhos.iss || exit /b 1

echo.
echo Instalador: dist\instalador\Retalhos_Setup_%VERSAO%.exe
