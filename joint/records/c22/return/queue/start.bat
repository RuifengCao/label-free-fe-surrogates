@echo off
rem Development trials of the plastic T-stub surrogate on this laptop (exploratory work, not a gate).
rem   1. the first time only: makes a self-contained Python environment in this folder, no Anaconda:
rem      uv 0.13.7 (the copy already checked for another project) downloads Python 3.12 into _uv\python,
rem      creates .venv\ and installs torch (CUDA build), numpy and scipy into it
rem   2. starts runner.py, which runs the jobs in the queue folder one after another
rem Double-click this file, or run its full path in PowerShell. Closing the window stops everything.
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
if not exist results mkdir results
if not exist queue mkdir queue
set "LOG=%~dp0logs\setup_log.txt"
set "UV=%~dp0_uv\uv.exe"
set "PY=%~dp0.venv\Scripts\python.exe"
set "UV_PYTHON_INSTALL_DIR=%~dp0_uv\python"
set "UV_CACHE_DIR=%~dp0_uv\cache"
set "UV_PYTHON_PREFERENCE=only-managed"
if exist "%~dp0logs\env_ok.txt" goto :run
echo [1/3] Creating .venv with Python 3.12, downloaded into this folder...
echo ==== setup started %DATE% %TIME% >> "%LOG%"
nvidia-smi >> "%LOG%" 2>&1
"%UV%" venv --python 3.12 --allow-existing "%~dp0.venv" >> "%LOG%" 2>&1
if errorlevel 1 goto :fail
echo [2/3] Installing torch 2.12.1 with CUDA, numpy and scipy. The download is about 3 GB: 10 to 40 minutes...
echo ---- install, backend auto >> "%LOG%"
"%UV%" pip install --python "%PY%" --torch-backend auto "torch==2.12.1" "numpy==2.4.*" "scipy==1.18.*" >> "%LOG%" 2>&1
if not errorlevel 1 goto :check
echo ---- install, backend cu130 >> "%LOG%"
"%UV%" pip install --python "%PY%" --torch-backend cu130 "torch==2.12.1" "numpy==2.4.*" "scipy==1.18.*" >> "%LOG%" 2>&1
if not errorlevel 1 goto :check
echo ---- install, backend cu126 >> "%LOG%"
"%UV%" pip install --python "%PY%" --torch-backend cu126 "torch==2.12.1" "numpy==2.4.*" "scipy==1.18.*" >> "%LOG%" 2>&1
if errorlevel 1 goto :fail
:check
echo [3/3] Checking that torch sees the GPU...
"%PY%" -I "%~dp0check_gpu.py" >> "%LOG%" 2>&1
if not errorlevel 1 goto :env_ok
echo       torch does not see the GPU yet. Installing the CUDA 12.6 build instead: another download of about 3 GB...
echo ---- reinstall, backend cu126 >> "%LOG%"
"%UV%" pip install --python "%PY%" --reinstall-package torch --torch-backend cu126 "torch==2.12.1" "numpy==2.4.*" "scipy==1.18.*" >> "%LOG%" 2>&1
if errorlevel 1 goto :fail
"%PY%" -I "%~dp0check_gpu.py" >> "%LOG%" 2>&1
if errorlevel 1 goto :fail
:env_ok
echo ok %DATE% %TIME% > "%~dp0logs\env_ok.txt"
:run
echo Starting the job runner. Keep the laptop plugged in and the lid open.
echo Closing this window stops the runs.
"%PY%" -I "%~dp0runner.py"
echo.
echo The runner has stopped.
pause
exit /b 0
:fail
echo.
echo Something failed. Leave this window open and tell the operator. The log is logs\setup_log.txt; the operator can read it.
pause
exit /b 1
