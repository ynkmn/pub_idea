
@echo off
chcp 65001 > nul REM UTF-8 で表示する場合。バッチファイル自体もUTF-8 BOM付きで保存
REM chcp 932 > nul REM Shift-JIS で表示する場合。バッチファイル自体はShift-JISで保存

set "VENV_DIR=C:\Users\YourUser\YourProject\venv"
set "SCRIPT_DIR=C:\Users\YourUser\YourProject"
set "PYTHON_SCRIPT=bayes_program.py"

REM 並列数を取得
REM %1 はバッチファイルの1番目の引数
set "PARALLEL_NUM=%1"

IF "%PARALLEL_NUM%"=="" (
    echo.
    echo エラー: 並列数が指定されていません。
    echo 使い方: %~nx0 ^<並列数^>
    echo 例: %~nx0 4
    echo.
    pause
    exit /b 1
)

echo 仮想環境をアクティベート中...
call "%VENV_DIR%\Scripts\activate.bat"

IF EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo 仮想環境がアクティベートされました。
    echo Pythonスクリプトを実行中: %PYTHON_SCRIPT% (並列数: %PARALLEL_NUM%)
    cd /d "%SCRIPT_DIR%"
    set PYTHONIOENCODING=utf-8

    REM Pythonスクリプトに引数として並列数を渡す
    python "%PYTHON_SCRIPT%" --parallel %PARALLEL_NUM%
    REM もしくは、引数名がない場合は python "%PYTHON_SCRIPT%" %PARALLEL_NUM%
) ELSE (
    echo エラー: 指定されたvenvのパスにactivate.batが見つかりません。
    echo パスを確認してください: %VENV_DIR%\Scripts\activate.bat
)

echo 完了。
pause





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
