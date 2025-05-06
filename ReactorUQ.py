import pymc as pm
import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt

# ツール情報
TOOL_NAME = "ReactorUQ_simplified"
VERSION = "0.1.0"

# 0. ロギング・エラーハンドリングの基本 (簡易版)
def log_message(message):
    """簡単なログメッセージを表示します。"""
    print(f"[{TOOL_NAME} LOG]: {message}")

def handle_error(error_message):
    """簡単なエラーメッセージを表示します。"""
    print(f"[{TOOL_NAME} ERROR]: {error_message}")
    # 本来はここで詳細なエラー処理や例外送出を行う

# 1. データ管理機能 (簡易版：ダミーデータ生成)
def generate_dummy_data(num_points=100, seed=42):
    """
    ダミーの実験データを生成します。
    反応度 = a_true * fuel_temp + b_true * coolant_temp + noise
    """
    log_message("ダミーデータの生成を開始します。")
    np.random.seed(seed)

    # 真のパラメータ
    a_true = 0.05
    b_true = -0.02
    sigma_true = 0.5 # 観測ノイズの標準偏差

    fuel_temp = np.linspace(300, 800, num_points)  # 燃料温度 (K)
    coolant_temp = np.linspace(280, 350, num_points) + np.random.normal(0, 10, num_points) # 冷却材温度 (K)

    # ノイズを含まない反応度
    reactivity_true = a_true * (fuel_temp - 550) + b_true * (coolant_temp - 315) # 中心化して係数の意味を明確に

    # 観測ノイズを加える
    observed_reactivity = reactivity_true + np.random.normal(0, sigma_true, num_points)

    data = pd.DataFrame({
        'fuel_temperature': fuel_temp,
        'coolant_temperature': coolant_temp,
        'observed_reactivity': observed_reactivity
    })
    log_message(f"ダミーデータ ({num_points}点) を生成しました。")
    log_message(f"使用した真のパラメータ: a={a_true}, b={b_true}, sigma_obs={sigma_true}")
    return data

# 2. モデル組み込み機能
def reactivity_model(fuel_temp, coolant_temp, params):
    """
    反応度モデル関数。
    反応度 = a * (燃料温度 - ref_fuel_temp) + b * (冷却材温度 - ref_coolant_temp)
    """
    # パラメータの参照温度（係数の解釈を容易にするため）
    ref_fuel_temp = 550
    ref_coolant_temp = 315
    
    a = params['a']
    b = params['b']
    
    return a * (fuel_temp - ref_fuel_temp) + b * (coolant_temp - ref_coolant_temp)

# 3. 誤差評価機能 (PyMCモデル内で尤度として組み込まれる)
#    ここではMSEやMAEを直接計算する関数は実装せず、ベイズモデルの尤度定義で誤差を扱う。

# 4. パラメータ設定・管理機能 (簡易版：コード内で定義)
def get_parameter_priors():
    """推定対象パラメータの事前分布情報を返します。"""
    log_message("パラメータの事前分布を設定します。")
    # ここではPyMCモデル内で直接定義するが、将来的にはYAML/JSONから読み込む
    priors = {
        'a': {'dist': 'Normal', 'mu': 0, 'sigma': 0.1},
        'b': {'dist': 'Normal', 'mu': 0, 'sigma': 0.1},
        'sigma_obs': {'dist': 'HalfNormal', 'sigma': 1.0} # 観測誤差の標準偏差
    }
    return priors

# 5. ベイズ推定エンジン（PyMC）
def run_bayesian_estimation(data, model_func, param_priors_info):
    """
    PyMCを使用してベイズ推定を実行し、事後分布を取得します。
    """
    log_message("ベイズ推定を開始します。")

    fuel_temp_obs = data['fuel_temperature'].values
    coolant_temp_obs = data['coolant_temperature'].values
    reactivity_obs = data['observed_reactivity'].values

    with pm.Model() as reactor_model:
        # 事前分布の設定
        # `a`: 燃料温度係数
        a_prior = param_priors_info['a']
        a = pm.Normal('a', mu=a_prior['mu'], sigma=a_prior['sigma'])

        # `b`: 冷却材温度係数
        b_prior = param_priors_info['b']
        b = pm.Normal('b', mu=b_prior['mu'], sigma=b_prior['sigma'])

        # 観測誤差の標準偏差
        sigma_obs_prior = param_priors_info['sigma_obs']
        sigma_obs = pm.HalfNormal('sigma_obs', sigma=sigma_obs_prior['sigma'])

        # モデルによる反応度の期待値
        # モデル関数に渡すパラメータの辞書を作成
        # PyMCのシンボリック変数を使用
        current_params = {'a': a, 'b': b}
        
        # PyMCモデル内でモデル関数を直接呼び出す代わりに、数式を記述
        # 反応度 = a * (燃料温度 - ref_fuel_temp) + b * (冷却材温度 - ref_coolant_temp)
        ref_fuel_temp = 550  # モデル定義と合わせる
        ref_coolant_temp = 315 # モデル定義と合わせる
        
        mu = a * (fuel_temp_obs - ref_fuel_temp) + b * (coolant_temp_obs - ref_coolant_temp)

        # 尤度: 観測された反応度
        # 二乗誤差は正規分布の尤度として暗黙的に考慮される
        observed = pm.Normal('observed_reactivity', mu=mu, sigma=sigma_obs, observed=reactivity_obs)

        # MCMCサンプリング
        log_message("MCMCサンプリングを実行します...")
        # trace = pm.sample(2000, tune=1000, cores=1, return_inferencedata=True, target_accept=0.9)
        # PyMC v5.x以降ではidata_kwargsで初期化戦略を指定することが推奨される場合がある
        trace = pm.sample(draws=2000, tune=1000, chains=2, cores=1, return_inferencedata=True, target_accept=0.9, random_seed=seed)
        # 警告が出る場合があるが、簡単な例なので無視。本番では要確認。

        log_message("MCMCサンプリングが完了しました。")

    return trace

# 6. 結果出力・可視化機能
def visualize_results(trace, params_to_plot):
    """
    推定結果（トレースプロット、事後分布など）を可視化します。
    """
    log_message("結果の可視化を開始します。")

    if trace is None:
        handle_error("トレースデータがありません。可視化をスキップします。")
        return

    # トレースプロット
    try:
        az.plot_trace(trace, var_names=params_to_plot)
        plt.suptitle(f"{TOOL_NAME} - Trace Plot", y=1.02)
        plt.tight_layout()
        plt.show()
        log_message("トレースプロットを表示しました。")
    except Exception as e:
        handle_error(f"トレースプロットの生成に失敗しました: {e}")


    # 事後分布の要約統計量
    try:
        summary = az.summary(trace, var_names=params_to_plot, hdi_prob=0.95)
        log_message("事後分布の要約統計量:")
        print(summary)
        # 結果をCSVなどに出力する場合はここで行う
        # summary.to_csv("posterior_summary.csv")
    except Exception as e:
        handle_error(f"事後分布サマリーの生成に失敗しました: {e}")

    # ペアプロット（相関図）
    try:
        az.plot_pair(trace, var_names=params_to_plot, kind='kde', divergences=True)
        plt.suptitle(f"{TOOL_NAME} - Pair Plot", y=1.02)
        plt.tight_layout()
        plt.show()
        log_message("ペアプロット（相関図）を表示しました。")
    except Exception as e:
        handle_error(f"ペアプロットの生成に失敗しました: {e}")


if __name__ == "__main__":
    log_message(f"ツール {TOOL_NAME} v{VERSION} を起動します。")
    seed = 123 # MCMCのseed

    # 1. データ準備
    experimental_data = generate_dummy_data(num_points=200, seed=seed)
    log_message("実験データ (最初の5行):")
    print(experimental_data.head())
    print("-" * 30)

    # 2. モデル関数は `reactivity_model` として定義済み

    # 4. パラメータ事前分布設定
    parameter_priors = get_parameter_priors()
    log_message("使用する事前分布:")
    for p, val in parameter_priors.items():
        print(f"  {p}: {val}")
    print("-" * 30)

    # 5. ベイズ推定実行
    #   推定対象のパラメータ名はPyMCモデル内で定義したものと一致させる
    parameters_for_estimation = ['a', 'b', 'sigma_obs']
    try:
        inference_data = run_bayesian_estimation(
            experimental_data,
            reactivity_model, # run_bayesian_estimation 内では直接使っていないが、概念として渡す
            parameter_priors
        )
    except Exception as e:
        handle_error(f"ベイズ推定中にエラーが発生しました: {e}")
        inference_data = None

    # 6. 結果出力・可視化
    if inference_data:
        visualize_results(inference_data, params_to_plot=parameters_for_estimation)
    else:
        log_message("推定データがないため、結果の表示をスキップします。")

    log_message(f"ツール {TOOL_NAME} の処理を終了します。")

