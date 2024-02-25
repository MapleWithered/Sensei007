@echo off

if not defined TAG (
    set TAG=1
    start wt -p "Windows PowerShell" %0
    :: Windows Terminal 中 cmd 的配置名，我这里是“cmd”
    exit
)

@REM 切换至当前bat所在位置
cd>nul 2>nul /D %~dp0
call venv\Scripts\activate.bat

TITLE Sensei007

:pystart
python main_daemon.py
goto pystart

pause