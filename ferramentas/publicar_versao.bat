@echo off
rem Publica a versao atual (instalador + versao.json) no GitHub e na pasta da rede.
rem Antes: suba a versao em retalhos\__init__.py e escreva o que mudou em instalador\novidades.md
setlocal
cd /d "%~dp0.."
set PY=.venv\Scripts\python.exe
if not exist "%PY%" set PY=python
%PY% ferramentas\publicar_versao.py %*
pause
