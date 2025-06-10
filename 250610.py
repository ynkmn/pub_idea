import pymc as pm
import pytensor.tensor as pt

# 観測データ（例）
# ... observed_reactivity, temp_data は事前に準備 ...

# logp関数を定義
def logp(observed_value, params, temp_data, sigma):
    """
    CustomDistのための対数確率関数
    
    Args:
        observed_value: 観測データ (PyMCが自動で渡す)
        params:         モデルの確率変数 (fuel_coef, coolant_coef)
        temp_data:      その他の入力データ
        sigma:          誤差の標準偏差
    
    Returns:
        対数確率
    """
    # pytensor.Opを使って、外部のPython関数(run_fortran_simulator)をPyMCの計算グラフに組み込む
    # このOpは、numpy配列を受け取り、numpy配列を返す関数をラップする
    @pt.as_op(itypes=[pt.dvector], otypes=[pt.dvector])
    def pymc_fortran_caller(p):
        # この関数がMCMCの各ステップで実行される
        predicted = run_fortran_simulator(p, temp_data)
        if predicted is None:
            # シミュレーション失敗時は非常に小さい尤度を返すため、
            # 観測値と全く異なるダミー値を返す
            return np.full_like(observed_value, -1e10)
        return predicted

    # ラップした関数を呼び出す
    predicted_reactivity = pymc_fortran_caller(params)

    # 観測値と予測値から対数尤度を計算
    return pm.Normal.logp(observed_value, mu=predicted_reactivity, sigma=sigma)


# PyMCモデルの定義
with pm.Model() as model:
    # パラメータの事前分布
    fuel_coef = pm.Uniform("fuel_temp_coef", -5.0, 0.0)
    coolant_coef = pm.Uniform("coolant_temp_coef", -3.0, 0.0)
    
    # パラメータを一つのベクトルにまとめる
    # pt.stack はPyTensorの関数で、テンソルを結合する
    params_vec = pt.stack([fuel_coef, coolant_coef])
    
    # 測定誤差の事前分布
    sigma = pm.HalfNormal("sigma", sigma=10.0)

    # CustomDistを使って尤度を定義
    pm.CustomDist(
        "likelihood",
        params_vec,       # logpの第2引数(params)に渡される
        temp_data,        # logpの第3引数(temp_data)に渡される
        sigma,            # logpの第4引数(sigma)に渡される
        logp=logp,
        observed=observed_reactivity # logpの第1引数(observed_value)に渡される
    )

# MCMCサンプリングの実行
with model:
    idata = pm.sample()





import subprocess
import numpy as np
import os

def run_fortran_simulator(params: np.ndarray, temp_data: np.ndarray) -> np.ndarray:
    """
    Fortran実行ファイルを呼び出し、シミュレーション結果を取得するラッパー関数

    Args:
        params (np.ndarray): [fuel_temp_coef, coolant_temp_coef] のようなパラメータ配列
        temp_data (np.ndarray): シミュレーションに必要なその他の入力データ（例：温度）

    Returns:
        np.ndarray: Fortranが計算した反応度の配列
    """
    # 一意なファイル名で実行の衝突を避ける（並列実行時に重要）
    pid = os.getpid()
    input_filename = f"input_{pid}.dat"
    output_filename = f"output_{pid}.dat"

    try:
        # 1. Fortran用の入力ファイルを作成
        with open(input_filename, "w") as f:
            # パラメータを書き込む
            f.write(f"{params[0]:.10f}\n")
            f.write(f"{params[1]:.10f}\n")
            # 必要であれば他のデータも書き込む
            # np.savetxt(f, temp_data, fmt="%.10f")

        # 2. subprocessでFortran実行ファイルを呼び出す
        # (Windowsの場合は 'reactor_sim.exe', Linux/Macでは './reactor_sim')
        command = ["./reactor_sim"] # 実行ファイル名は適宜変更してください
        subprocess.run(command, check=True, timeout=300) # タイムアウトを設定

        # 3. Fortranが出力した結果ファイルを読み込む
        predicted_reactivity = np.loadtxt(output_filename)
        return predicted_reactivity

    except subprocess.CalledProcessError as e:
        print(f"Fortranの実行に失敗しました: {e}")
        # エラー時は尤度が非常に低くなるようにNoneを返す
        return None
    except FileNotFoundError:
        print(f"結果ファイル {output_filename} が見つかりません。")
        return None
    finally:
        # 4. 一時ファイルをクリーンアップ
        if os.path.exists(input_filename):
            os.remove(input_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)





! reactivity_calc.f90
subroutine calculate_reactivity(params, temp_data, reactivity, n_points)
    implicit none
    integer, intent(in) :: n_points
    double precision, intent(in) :: params(2)         ! [fuel_temp_coef, coolant_temp_coef]
    double precision, intent(in) :: temp_data(n_points, 2) ! [fuel_temp, coolant_temp]
    double precision, intent(out) :: reactivity(n_points)

    ! 反応度を計算
    reactivity = params(1) * temp_data(:, 1) + params(2) * temp_data(:, 2)
end subroutine calculate_reactivity


import pymc as pm
import numpy as np
import pytensor.tensor as pt
from fortran_model import calculate_reactivity # f2pyで生成したモジュール

# 観測データ（例）
time_data = np.linspace(0, 100, 101)
fuel_temp = 300 + 50 * (1 - np.exp(-time_data / 20))
coolant_temp = 290 + 30 * (1 - np.exp(-time_data / 30))
true_reactivity = -2.0 * fuel_temp - 1.5 * coolant_temp
observed_reactivity = true_reactivity + np.random.normal(0, 10, len(time_data))

# BlackBoxLikelihoodに渡す対数尤度関数
def loglike(params):
    # params: PyMCがサンプリングしたパラメータ [fuel_temp_coef, coolant_temp_coef]
    
    # Fortranモデルを呼び出して反応度を計算
    # (ここではダミーの計算。実際にはf2pyの関数を呼び出す)
    predicted_reactivity = params[0] * fuel_temp + params[1] * coolant_temp
    
    # 観測データとの対数尤度を計算（正規分布を仮定）
    # PyMC v5では、logpはpt.sum()で合計する必要がある
    log_likelihood = pm.Normal.logp(observed_reactivity, mu=predicted_reactivity, sigma=10.0)
    return pt.sum(log_likelihood)


with pm.Model() as pymc_model:
    # 1. パラメータの事前分布を定義
    fuel_coef = pm.Uniform("fuel_temp_coef", -5.0, 0.0)
    coolant_coef = pm.Uniform("coolant_temp_coef", -3.0, 0.0)
    
    # 2. BlackBoxLikelihoodを使ってFortranモデルを尤度に組み込む
    pm.BlackBoxLikelihood(
        "likelihood",
        loglike,
        observes=observed_reactivity,
        inputs=[fuel_coef, coolant_coef], # loglike関数に渡すパラメータ
    )


