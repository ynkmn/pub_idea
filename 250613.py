import pymc as pm
import numpy as np
import arviz as az
import pytensor.tensor as pt
import matplotlib.pyplot as plt

# --- 1. ブラックボックスとなる解析コード群（ユーザーが用意する部分） ---

# @pm.pytensorf.as_op デコレータを使って、Python関数をPyTensorの演算に変換
@pm.pytensorf.as_op(
    # itypes: 入力変数の型を指定 (dscalar = double precision scalar)
    itypes=[pt.dscalar, pt.dscalar], 
    # otypes: 出力変数の型を指定 (dvector = double precision vector)
    otypes=[pt.dvector]
)
def run_full_analysis(fuel_temp_coef, coolant_temp_coef):
    """
    MCMCの各ステップで呼び出される、全体のブラックボックス関数。
    この関数自体は、純粋なPython/Numpyで記述する。
    """
    # ステップA: 温度係数を基に、解析コードを実行して温度分布を再評価
    # 【重要】ここはユーザーの重い解析コードの呼び出しに相当
    time = np.linspace(0, 100, 101)
    base_fuel_temp = 300 + 50 * (1 - np.exp(-time / 20))
    base_coolant_temp = 290 + 30 * (1 - np.exp(-time / 30))
    
    new_fuel_temp = base_fuel_temp * (1 + (fuel_temp_coef + 2.0) * 0.01)
    new_coolant_temp = base_coolant_temp * (1 + (coolant_temp_coef + 1.5) * 0.01)
    
    # ステップB: 新しい温度分布と温度係数から、反応度を計算
    predicted_reactivity = (fuel_temp_coef * new_fuel_temp) + (coolant_temp_coef * new_coolant_temp)
    
    # otypesで指定した通りのNumpy配列を返す
    return predicted_reactivity.astype(np.float64)

# --- 2. データの準備 ---
# 「真の」反応度データ（観測データ）を一度だけ生成する
true_fuel_temp_coef = -2.0
true_coolant_temp_coef = -1.5
# `run_full_analysis`はNumpy配列を返すので、そのままでOK
true_reactivity = run_full_analysis(true_fuel_temp_coef, true_coolant_temp_coef)
observed_reactivity = true_reactivity + np.random.normal(0, 10, len(true_reactivity))

# --- 3. PyMCモデルの定義 ---
# logp_funcは不要になり、モデルの記述が簡潔になる
with pm.Model() as reactor_model_with_recalc:
    # パラメータの事前分布を定義
    fuel_temp_coef = pm.Uniform("fuel_temp_coef", lower=-5.0, upper=0.0)
    coolant_temp_coef = pm.Uniform("coolant_temp_coef", lower=-3.0, upper=0.0)
    sigma = pm.HalfNormal("sigma", sigma=20)

    # デコレータで変換した関数をモデル内で直接呼び出す
    predicted_reactivity = run_full_analysis(fuel_temp_coef, coolant_temp_coef)

    # 尤度を定義
    pm.Normal("likelihood", mu=predicted_reactivity, sigma=sigma, observed=observed_reactivity)

# --- 4. サンプリングの実行 ---
with reactor_model_with_recalc:
    idata = pm.sample(1000, tune=500, cores=1, chains=2)

# --- 5. 結果の確認 ---
print(az.summary(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"]))
az.plot_posterior(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"])
plt.show()





import pymc as pm
import numpy as np
import arviz as az
import pytensor.tensor as pt
import matplotlib.pyplot as plt

# --- 1. ブラックボックスとなる解析コード群（ユーザーが用意する部分） ---

def execute_thermal_analysis_code(fuel_temp_coef, coolant_temp_coef):
    """
    【重要】ここに、温度係数を入力として新しい温度分布を計算する、
    ユーザーの重い解析コード（例: 連続エネルギーモンテカルロコード、熱流動コード）が入る。
    
    この例では、ダミーの計算で代用する。
    係数に応じてベースの温度が少し変化すると仮定。
    """
    # (仮の計算) ベースとなる温度分布を生成
    time = np.linspace(0, 100, 101)
    base_fuel_temp = 300 + 50 * (1 - np.exp(-time / 20))
    base_coolant_temp = 290 + 30 * (1 - np.exp(-time / 30))
    
    # (仮の計算) 係数が温度分布に与える影響を模擬
    # 本来は、ここがシミュレーション結果で置き換わる
    new_fuel_temp = base_fuel_temp * (1 + (fuel_temp_coef + 2.0) * 0.01) 
    new_coolant_temp = base_coolant_temp * (1 + (coolant_temp_coef + 1.5) * 0.01)
    
    return new_fuel_temp, new_coolant_temp

def run_full_analysis(fuel_temp_coef, coolant_temp_coef):
    """
    MCMCの各ステップで呼び出される、全体のブラックボックス関数。
    """
    # ステップA: 温度係数を基に、解析コードを実行して温度分布を再評価
    new_fuel_temp, new_coolant_temp = execute_thermal_analysis_code(
        fuel_temp_coef, coolant_temp_coef
    )
    
    # ステップB: 新しい温度分布と温度係数から、反応度を計算
    # [span_2](start_span)この部分は reactor_uq_tool.txt の LinearReactivityModel に相当[span_2](end_span)
    predicted_reactivity = (fuel_temp_coef * new_fuel_temp) + (coolant_temp_coef * new_coolant_temp)
    
    return predicted_reactivity

# --- 2. PyTensorラッパーと対数尤度関数 ---

def logp_func(obs, fuel_temp_coef, coolant_temp_coef, sigma):
    """
    観測データ(obs)とパラメータを受け取り、対数尤度を計算する関数
    """
    # ブラックボックス関数をPyTensorの演算としてラップする
    predicted_reactivity = pm.pytensorf.OpFromGraph(
        [fuel_temp_coef, coolant_temp_coef],
        lambda f, c: run_full_analysis(f, c)
    )(fuel_temp_coef, coolant_temp_coef)

    # 観測値と予測値から対数尤度を計算
    return pm.logp(pm.Normal.dist(mu=predicted_reactivity, sigma=sigma), obs)

# --- 3. データの準備 ---
# 「真の」反応度データ（観測データ）を一度だけ生成する
true_fuel_temp_coef = -2.0
true_coolant_temp_coef = -1.5
true_fuel_temp, true_coolant_temp = execute_thermal_analysis_code(true_fuel_temp_coef, true_coolant_temp_coef)
true_reactivity = (true_fuel_temp_coef * true_fuel_temp) + (true_coolant_temp_coef * true_coolant_temp)
observed_reactivity = true_reactivity + np.random.normal(0, 10, len(true_reactivity))

# --- 4. PyMCモデルの定義 ---
with pm.Model() as reactor_model_with_recalc:
    # パラメータの事前分布を定義
    fuel_temp_coef = pm.Uniform("fuel_temp_coef", lower=-5.0, upper=0.0)
    coolant_temp_coef = pm.Uniform("coolant_temp_coef", lower=-3.0, upper=0.0)
    sigma = pm.HalfNormal("sigma", sigma=20)

    # カスタム対数尤度関数をモデルに追加
    pm.Potential(
        "likelihood",
        logp_func(
            observed_reactivity,
            fuel_temp_coef,
            coolant_temp_coef,
            sigma
        )
    )

# --- 5. サンプリングの実行 ---
with reactor_model_with_recalc:
    # MCMCサンプリングを実行。解析コードが重いため、時間はかかる可能性がある
    idata = pm.sample(1000, tune=500, cores=1, chains=2)

# --- 6. 結果の確認 ---
print(az.summary(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"]))
az.plot_posterior(idata, var_names=["fuel_temp_coef", "coolant_temp_coef", "sigma"])
plt.show()




“If you want your custom function to be differentiable, you should subclass Op and implement the grad method rather than using as_op.”