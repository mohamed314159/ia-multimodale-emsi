@echo off
rem Lance le téléchargement Classroom (utilisé par le Planificateur de tâches Windows).
rem La sortie est écrite dans dernier_lancement.log, à côté de ce fichier.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."

set PY=python
if exist "lab_autoencoder_2\.venv\Scripts\python.exe" set PY=lab_autoencoder_2\.venv\Scripts\python.exe

echo === %date% %time% === > "%~dp0dernier_lancement.log"
"%PY%" classroom_download\download_classroom.py >> "%~dp0dernier_lancement.log" 2>&1
