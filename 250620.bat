
from pathlib import Path

folder = Path("対象フォルダのパス")
threshold = 500 * 1024 * 1024  # 500MB（バイト単位）

for file in folder.glob("*.dat"):
    if file.is_file() and file.stat().st_size >= threshold:
        file.unlink()  # ファイルを削除
        print(f"削除: {file} ({file.stat().st_size / (1024*1024):.1f} MB)")




import pandas as pd
import os
import time

df.to_csv("sample.csv")
for _ in range(5):
    if os.path.isfile("sample.csv"):
        with open("sample.csv") as f:
            # 処理
        break
    else:
        time.sleep(0.1)
else:
    raise FileNotFoundError("sample.csvが見つかりません")



def objective(trial):
    try:
        # Fortranプログラムの実行
        # ポスト処理（ファイル読み込みなど）
        return 評価値
    except FileNotFoundError:
        # ファイルが見つからない場合は試行失敗として扱う
        trial.set_user_attr("error", "file_not_found")
        raise optuna.TrialPruned()  # または trial.fail()





import argparse
import multiprocessing
import os # osモジュールをインポート

def run_bayesian_inference(parallel_num, template_dir):
    print(f"ベイズ推定を開始します。並列数: {parallel_num}")
    print(f"使用するテンプレートフォルダ: {template_dir}")

    # テンプレートフォルダが存在するか、Python側でも念のため確認
    if not os.path.isdir(template_dir):
        print(f"エラー: 指定されたテンプレートフォルダ '{template_dir}' が見つからないか、ディレクトリではありません。")
        return

    # ここにベイズ推定のロジックを実装
    # 例: multiprocessing.Pool を使用
    with multiprocessing.Pool(processes=parallel_num) as pool:
        # ダミーのタスク。実際にはテンプレートフォルダ内のファイルを読み込んだりする処理
        results = pool.map(lambda x: x*x, range(parallel_num * 10))
    print("ベイズ推定が完了しました。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ベイズ推定プログラム")
    parser.add_argument('--parallel', type=int, default=1,
                        help='並列処理のコア数')
    parser.add_argument('--template_dir', type=str, required=True, # 必須引数とする
                        help='解析コードのテンプレートフォルダのパス')

    args = parser.parse_args()
    
    if args.parallel <= 0:
        print("エラー: 並列数は1以上の整数を指定してください。")
    else:
        run_bayesian_inference(args.parallel, args.template_dir)






@echo off
chcp 65001 > nul REM UTF-8 で表示する場合。バッチファイル自体もUTF-8 BOM付きで保存
REM chcp 932 > nul REM Shift-JIS で表示する場合。バッチファイル自体はShift-JISで保存

set "VENV_DIR=C:\Users\YourUser\YourProject\venv"         REM venvのパスを適宜変更してください
set "SCRIPT_DIR=C:\Users\YourUser\YourProject"            REM Pythonスクリプトがあるディレクトリのパスを適宜変更してください
set "PYTHON_SCRIPT=bayes_program.py"                      REM 実行したいPythonスクリプト名に置き換えてください
set "TEMPLATE_FOLDER=C:\Users\YourUser\YourProject\templates" REM テンプレートフォルダのパスを適宜変更してください

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

---

## テンプレートフォルダの存在確認

echo テンプレートフォルダを確認中: %TEMPLATE_FOLDER%
IF NOT EXIST "%TEMPLATE_FOLDER%\" (
    echo エラー: 指定されたテンプレートフォルダが見つかりません。
    echo パスを確認してください: "%TEMPLATE_FOLDER%"
    pause
    exit /b 1
)
echo テンプレートフォルダが見つかりました。

---

echo 仮想環境をアクティベート中...
call "%VENV_DIR%\Scripts\activate.bat"

IF EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo 仮想環境がアクティベートされました。
    echo Pythonスクリプトを実行中: %PYTHON_SCRIPT% (並列数: %PARALLEL_NUM%)
    cd /d "%SCRIPT_DIR%"
    set PYTHONIOENCODING=utf-8

    REM Pythonスクリプトに引数として並列数とテンプレートフォルダのパスを渡す
    python "%PYTHON_SCRIPT%" --parallel %PARALLEL_NUM% --template_dir "%TEMPLATE_FOLDER%"
) ELSE (
    echo エラー: 指定されたvenvのパスにactivate.batが見つかりません。
    echo パスを確認してください: %VENV_DIR%\Scripts\activate.bat
    pause
    exit /b 1
)

echo 完了。
pause




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
