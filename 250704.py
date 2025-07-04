import subprocess
import pandas as pd
import os

class AnalysisCoupling:
    """
    ベイズ最適化と外部解析コードを連携させるためのクラス。

    Attributes:
        analysis_command (list): 実行する解析コマンドと引数のリスト。
        input_template_path (str): 入力ファイルのテンプレートのパス。
        input_filename (str): 生成する入力ファイルの名前。
        output_filepath (str): 解析コードが出力する結果ファイルのパス。
    """

    def __init__(self, analysis_command, input_template_path, input_filename, output_filepath):
        """
        クラスを初期化する。

        Args:
            analysis_command (list): 例: ["python", "simple_solver.py"]
            input_template_path (str): 例: "input_template.txt"
            input_filename (str): 例: "analysis_input.txt"
            output_filepath (str): 例: "results/output.csv"
        """
        self.analysis_command = analysis_command
        self.input_template_path = input_template_path
        self.input_filename = input_filename
        self.output_filepath = output_filepath

        # 結果を保存するディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(self.output_filepath), exist_ok=True)

    def _create_input_file(self, params):
        """
        設計パラメータから解析用の入力ファイルを生成する（プライベートメソッド）。

        Args:
            params (dict): 設計パラメータの辞書。例: {'param1': 1.5, 'param2': 100}
        """
        with open(self.input_template_path, 'r') as f:
            template = f.read()

        # テンプレートにパラメータを埋め込む
        input_content = template.format(**params)

        with open(self.input_filename, 'w') as f:
            f.write(input_content)

    def run_analysis(self):
        """
        外部の解析コマンドを実行する。
        """
        # コマンドに引数（入力ファイル名）を追加
        command = self.analysis_command + [self.input_filename, self.output_filepath]
        
        print(f"実行コマンド: {' '.join(command)}")
        
        try:
            # サブプロセスとして解析を実行し、完了を待つ
            subprocess.run(command, check=True, capture_output=True, text=True)
            print("解析が正常に終了しました。")
            return True
        except subprocess.CalledProcessError as e:
            print(f"解析エラーが発生しました。")
            print(f"コマンド: {e.cmd}")
            print(f"リターンコード: {e.returncode}")
            print(f"標準出力: {e.stdout}")
            print(f"標準エラー: {e.stderr}")
            return False

    def post_process(self):
        """
        解析結果ファイルを読み込み、目的関数の値を計算する。
        
        Returns:
            float: 最適化の目的関数となる評価値。
                   ファイルが存在しない、または空の場合は大きなペナルティ値を返す。
        """
        if not os.path.exists(self.output_filepath):
            print("エラー: 出力ファイルが見つかりません。")
            return 1e10  # ペナルティ値

        try:
            # 例として、CSVファイルを読み込み、'objective'列の最小値を目的とする
            df = pd.read_csv(self.output_filepath)
            if df.empty:
                print("警告: 出力ファイルが空です。")
                return 1e10 # ペナルティ値
            
            # ここに目的関数を計算するロジックを実装
            # 例：応力の最大値を最小化したい場合、-stress_maxを返す（最大化問題にするため）
            # 例：効率を最大化したい場合、efficiencyをそのまま返す
            objective_value = df['objective_value'].min()
            print(f"目的関数の値: {objective_value}")
            return objective_value
            
        except Exception as e:
            print(f"ポスト処理中にエラーが発生しました: {e}")
            return 1e10 # ペナルティ値

    def evaluate(self, **params):
        """
        一連の解析と評価を実行する。ベイズ最適化の目的関数として使用する。

        Args:
            params (dict): ベイズ最適化システムから渡される設計パラメータ。

        Returns:
            float: 評価値。ベイズ最適化は通常「最大化」を目指すため、
                   最小化が目的の場合は符号を反転させるなどの調整が必要。
        """
        print("-" * 50)
        print(f"評価開始: パラメータ = {params}")
        
        # 1. 入力ファイルの生成
        self._create_input_file(params)

        # 2. 解析の実行
        success = self.run_analysis()

        # 3. ポスト処理と評価値の返却
        if success:
            objective = self.post_process()
            # ベイズ最適化ライブラリが「最大化」を前提とする場合、
            # 最小化したい目的関数（例：損失）は符号を反転させる
            return -objective
        else:
            # 解析失敗時はペナルティ値を返す（-1e10など）
            return -1e10

from bayesian_optimization import BayesianOptimization
from analysis_coupling import AnalysisCoupling

# 1. 解析連携クラスのインスタンスを作成
#    実際の解析プログラム（例: /opt/solver/run.sh）に合わせてコマンドを修正
analysis_handler = AnalysisCoupling(
    analysis_command=["python", "simple_solver.py"],
    input_template_path="input_template.txt",
    input_filename="simulation.in",
    output_filepath="results/output.csv"
)

# 2. ベイズ最適化のパラメータ探索範囲を定義
#    キーは 'input_template.txt' のプレースホルダ名と一致させる
pbounds = {
    'param1': (0.0, 5.0),  # パラメータ1の範囲
    'param2': (0, 50),     # パラメータ2の範囲
}

# 3. ベイズ最適化オブジェクトを生成
#    目的関数として、クラスの `evaluate` メソッドを渡す
optimizer = BayesianOptimization(
    f=analysis_handler.evaluate,
    pbounds=pbounds,
    random_state=1,
    verbose=2 # ログの出力レベル (2: 詳細, 1: 簡易, 0: なし)
)

# 4. 最適化を実行
#    init_points: 初期探索点数, n_iter: 最適化の繰り返し回数
optimizer.maximize(
    init_points=5,
    n_iter=20
)

# 5. 最適化結果の表示
print("\n最適化完了！")
print(f"最適パラメータ: {optimizer.max['params']}")
print(f"目的関数の最大値: {-optimizer.max['target']}") # evaluateで符号反転したため、戻す


with open('file.txt', 'r', encoding='utf-8') as file:
    content = file.read()

new_content = content.replace('置換前の文字列', '置換後の文字列')

with open('file.txt', 'w', encoding='utf-8') as file:
    file.write(new_content)



lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
chunk_size = 4
result = [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]
print(result)
# 出力: [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]
