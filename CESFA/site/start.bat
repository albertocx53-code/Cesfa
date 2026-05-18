@echo off
title CESFA Sistema

echo ================================
echo INICIANDO CESFA SISTEMA
echo ================================

cd /d %~dp0

python -m pip install --upgrade pip

pip install fastapi "uvicorn[standard]" jinja2 python-multipart sqlalchemy passlib bcrypt==4.0.1 python-jose

cls

echo ================================
echo SISTEMA INICIADO
echo ================================
echo.
echo Abra:
echo http://127.0.0.1:8000
echo.

uvicorn main:app --reload

pause
