@echo off
set "VENV_DIR=C:\Users\YourUser\YourProject\venv"  REM venvのパスを適宜変更してください
set "SCRIPT_DIR=C:\Users\YourUser\YourProject"     REM Pythonスクリプトがあるディレクトリのパスを適宜変更してください
set "PYTHON_SCRIPT=your_script.py"                REM 実行したいPythonスクリプト名に置き換えてください

echo 仮想環境をアクティベート中...

REM venvのactivateスクリプトを実行
call "%VENV_DIR%\Scripts\activate.bat"

IF EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo 仮想環境がアクティベートされました。
    echo Pythonスクリプトを実行中: %PYTHON_SCRIPT%
    cd /d "%SCRIPT_DIR%"
    python "%PYTHON_SCRIPT%"
) ELSE (
    echo エラー: 指定されたvenvのパスにactivate.batが見つかりません。
    echo パスを確認してください: %VENV_DIR%\Scripts\activate.bat
)

echo 完了。
pause
