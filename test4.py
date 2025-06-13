import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
from pytensor.graph import Op, Apply
import arviz as az
import subprocess # 外部プロセスを呼び出すため
import os # ファイルパス操作のため

# ---------------------------------------------------------------------------
# 0. テスト用の模擬データと外部コードの準備
# ---------------------------------------------------------------------------
# このセクションは、実行可能なサンプルにするための準備です。
# 実際には、ユーザー自身の観測データと解析コードを使用してください。

# 観測データの生成
time_data = np.linspace(0, 100, 101)
fuel_temp = 300 + 50 * (1 - np.exp(-time_data / 20))
coolant_temp = 290 + 30 * (1 - np.exp(-time_data / 30))

# 真のパラメータ値（本来は未知）
true_fuel_temp_coef = -2.0
true_coolant_temp_coef = -1.5

# ノイズを含む観測反応度データ
true_reactivity = true_fuel_temp_coef * fuel_temp + true_coolant_temp_coef * coolant_temp
observed_reactivity = true_reactivity + np.random.normal(0, 5, len(time_data))


# 外部解析コードの「フリ」をする関数
# 実際にはこの部分が `subprocess.run` でのexe呼び出しになります。
def simulate_external_code(fuel_coef: float, coolant_coef: float, output_path: str):
    """
    外部解析コード.exeの動作を模倣する。
    指定された係数で反応度を計算し、CSVファイルに書き出す。
    """
    # 実際のコードではここで物理シミュレーションが実行される
    predicted_reactivity = fuel_coef * fuel_temp + coolant_coef * coolant_temp
    pd.DataFrame({'reactivity': predicted_reactivity}).to_csv(output_path, index=False)


# ---------------------------------------------------------------------------
# 1. 外部コードを呼び出すための PyTensor Op を作成
# ---------------------------------------------------------------------------
class ReactivitySimulatorOp(Op):
    """
    PyTensorのOpとして外部解析コードをラップするクラス。

    このOpは入力として2つのスカラー（燃料と冷却材の温度係数）を受け取り、
    出力として1つのベクトル（計算された反応度）を返す。
    """

    # itypes: 入力変数の型を指定
    itypes = [pt.dscalar, pt.dscalar] 
    # otypes: 出力変数の型を指定
    otypes = [pt.dvector]

    def perform(self, node, inputs, output_storage):
        """
        Opの実際の計算処理を定義するメソッド。
        PyMCのサンプリング中に繰り返し呼び出される。
        """
        # inputsからパラメータ値を取得
        fuel_coef, coolant_coef = inputs

        # 外部プロセスに渡すためのユニークな出力ファイル名を生成
        # (並列実行時のファイル競合を避けるため)
        pid = os.getpid()
        temp_output_file = f'temp_reactivity_{pid}.csv'
        
        # --- ここで外部の実行可能ファイル（exe）を呼び出す ---
        # 例: 
        # command = [
        #     "path/to/your/解析コード.exe",
        #     "--fuel_coef", str(fuel_coef),
        #     "--coolant_coef", str(coolant_coef),
        #     "--output_file", temp_output_file
        # ]
        # subprocess.run(command, check=True, capture_output=True)
        
        # このサンプルでは、Python関数で代用
        simulate_external_code(fuel_coef, coolant_coef, temp_output_file)
        # --- 外部コードの呼び出し終了 ---

        # 外部コードが出力した結果ファイルを読み込む
        result_df = pd.read_csv(temp_output_file)
        predicted_reactivity = result_df['reactivity'].values

        # 結果をクリーンアップ
        os.remove(temp_output_file)

        # PyMC/PyTensorに計算結果を渡す
        output_storage[0][0] = predicted_reactivity

    # gradメソッドは定義しない。これにより、PyMCはこのOpが
    # 勾配情報を持たないことを認識し、勾配ベースのサンプラ（NUTS等）は使えなくなる。

# Opのインスタンスを作成
reactivity_simulator_op = ReactivitySimulatorOp()


# ---------------------------------------------------------------------------
# 2. pm.CustomDist で使用する対数尤度 (logp) 関数を定義
# ---------------------------------------------------------------------------
def logp_reactivity(observed_data, fuel_coef, coolant_coef, sigma):
    """
    カスタム尤度分布の対数尤度を計算する関数。
    
    Args:
        observed_data (np.ndarray): 観測された反応度データ
        fuel_coef (TensorVariable): 燃料温度係数
        coolant_coef (TensorVariable): 冷却材温度係数
        sigma (TensorVariable): 観測誤差の標準偏差

    Returns:
        TensorVariable: 計算された対数尤度
    """
    # Opを呼び出して、与えられた係数に対する反応度を予測
    predicted_reactivity = reactivity_simulator_op(fuel_coef, coolant_coef)
    
    # 観測データと予測データの差に基づき、正規分布の対数尤度を計算
    # pm.logp(分布, 観測値) を使うと簡単に記述できる
    return pm.logp(pm.Normal.dist(mu=predicted_reactivity, sigma=sigma), observed_data)


# ---------------------------------------------------------------------------
# 3. PyMCモデルの構築
# ---------------------------------------------------------------------------
with pm.Model() as reactor_model:
    # --- パラメータの事前分布を定義 ---
    # ユーザー提供のコードの範囲を参考にUniform分布を設定
    fuel_temp_coef = pm.Uniform("fuel_temp_coef", lower=-5.0, upper=0.0)
    coolant_temp_coef = pm.Uniform("coolant_temp_coef", lower=-3.0, upper=0.0)
    
    # 観測誤差の事前分布
    sigma = pm.HalfNormal("sigma", sigma=10) # 誤差のスケールはデータに応じて調整

    # --- カスタム尤度分布を定義 ---
    # pm.CustomDist を使い、自作のlogp関数と外部コードをモデルに組み込む
    likelihood = pm.CustomDist(
        "likelihood",
        fuel_temp_coef,         # logp関数に渡すパラメータ
        coolant_temp_coef,      # logp関数に渡すパラメータ
        sigma,                  # logp関数に渡すパラメータ
        logp=logp_reactivity,        # 使用するlogp関数
        observed=observed_reactivity # 観測データ
    )


# ---------------------------------------------------------------------------
# 4. MCMCサンプリングの実行
# ---------------------------------------------------------------------------
with reactor_model:
    # 【重要】
    # 外部コードは勾配情報を提供しないため、勾配不要なサンプラー（Metropolisなど）を指定する。
    # NUTSは使用できない。
    step = pm.Metropolis([fuel_temp_coef, coolant_temp_coef, sigma])

    # サンプリングを実行
    # 外部コードの呼び出しは遅いため、最初は少ないサンプル数で試すことを推奨
    print("MCMCサンプリングを開始します（外部コードを繰り返し呼び出すため時間がかかります）...")
    idata = pm.sample(draws=2000, tune=1000, step=step, cores=1)
    print("サンプリングが完了しました。")


# ---------------------------------------------------------------------------
# 5. 結果の確認
# ---------------------------------------------------------------------------
# ArviZを使って結果の要約統計量を表示
# mcse_sdが実効サンプルサイズ(ess_bulk)に対して小さいことを確認
summary = az.summary(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"])
print(summary)

# トレースプロットを表示して、サンプリングが収束しているか視覚的に確認
az.plot_trace(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"])
plt.tight_layout()
plt.show()

# パラメータの事後分布をプロット
az.plot_posterior(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"])
plt.show()
