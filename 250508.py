import numpy as np
import pymc3 as pm
import arviz as az
import matplotlib.pyplot as plt
import warnings

# 将来のバージョンに関するPyMC3の警告を無視する設定
warnings.filterwarnings("ignore", category=FutureWarning)

# --- 1. シミュレーション設定とデータの準備 ---

# 時間設定
t_start = 0      # 開始時間 [s]
t_end = 20       # 終了時間 [s]
n_steps = 200    # 時間ステップ数
times = np.linspace(t_start, t_end, n_steps)

# 真のパラメータ値 (合成データ生成用)
# ここでは、燃料温度係数と冷却材温度係数の真値を仮定します
# 単位は例として dk/k / degC とします
true_alpha_fuel = -2.5e-5  # 真の燃料温度係数
true_alpha_coolant = -3.0e-5 # 真の冷却材温度係数
# 注意：この単純なモデル (同じDelta Tを入力とする) では、
# alpha_fuel と alpha_coolant は分離して推定するのが難しい (非識別の問題)。
# ベイズ推定では事後分布が強く相関する形で現れます。
# より複雑なモデルや、異なる時間応答を持つDelta T入力があれば分離可能です。

# 温度変化 ΔT (サインカーブとして与える)
# 簡単のため、燃料と冷却材で同じ温度変化と仮定します
amplitude_delta_T = 40   # 温度変化の振幅 [degC]
frequency_delta_T = 0.2  # 温度変化の周波数 [Hz]
delta_T = amplitude_delta_T * np.sin(2 * np.pi * frequency_delta_T * times)

# 合成「実験」データの生成
# モデル：反応度 = alpha_fuel * DeltaT_fuel + alpha_coolant * DeltaT_coolant
# 簡単のため、DeltaT_fuel = DeltaT_coolant = delta_T とします
true_reactivity = true_alpha_fuel * delta_T + true_alpha_coolant * delta_T

# 観測ノイズの追加 (正規分布ノイズを仮定)
observation_noise_std = 1e-5 # 観測ノイズの標準偏差 (例)
observed_reactivity = true_reactivity + np.random.normal(0, observation_noise_std, size=times.shape)

# 生成データのプロット (確認用)
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(times, delta_T)
plt.xlabel('Time [s]')
plt.ylabel('Delta T [°C]')
plt.title('Simulated Temperature Deviation Input')
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(times, true_reactivity, label='True Reactivity', linestyle='--')
plt.plot(times, observed_reactivity, label='Observed Reactivity (with noise)', alpha=0.7)
plt.xlabel('Time [s]')
plt.ylabel('Reactivity [dk/k]')
plt.title('Simulated Reactivity Data')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()


# --- 2. ベイズモデルの定義 (PyMC3) ---

print("PyMC3モデルを構築中...")
with pm.Model() as reactor_uq_model:
    # 推定したいパラメータの事前分布を定義
    # ここでは、広い範囲をカバーする正規分布を仮定します
    # 事前知識に基づいて適切に設定することが重要です
    # muは事前平均、sdは事前標準偏差
    alpha_fuel = pm.Normal('alpha_fuel', mu=0, sd=1e-4)
    alpha_coolant = pm.Normal('alpha_coolant', mu=0, sd=1e-4)

    # モデルからの予測値 (期待値) を定義
    # これは、現在のパラメータ値と入力データ (delta_T) から計算される反応度です
    # ここでは、delta_T_fuel = delta_T_coolant = delta_T としています
    mu = alpha_fuel * delta_T + alpha_coolant * delta_T

    # 観測データの尤度関数を定義
    # 観測データ observed_reactivity は、モデルの期待値 mu の周りに
    # 標準偏差 observation_noise_std の正規分布ノイズが乗っていると仮定します
    likelihood = pm.Normal('observed_reactivity', mu=mu, sd=observation_noise_std, observed=observed_reactivity)

    # モデルの定義はこれで完了です
    print("モデル構築完了。")

# --- 3. MCMCサンプリングの実行 ---

print("MCMCサンプリングを開始...")
# NUTSサンプラーを使用 (連続パラメータに適している)
# draws: ウォームアップ後のサンプル数
# tune: ウォームアップ (調整) のサンプル数
# chains: 独立したチェーン数
# cores: 使用するCPUコア数。pm.sampling.CPU_COUNT で利用可能なコア数を使用
# target_accept: 受容率の目標値 (NUTSで推奨)
# random_seed: 再現性のためのシード値 (オプション)

trace = pm.sample(
    draws=2000,
    tune=1000,
    chains=4,
    cores=pm.sampling.CPU_COUNT,
    target_accept=0.9,
    # random_seed=[123, 124, 125, 126] # 例
)
print("サンプリング完了。")


# --- 4. 結果の分析と可視化 (ArviZ) ---

print("結果を分析中...")

# サマリー統計の表示 (推定値の平均、標準偏差、信用区間、R-hatなど)
# hdi_prob: 最高密度区間 (HDI) の確率 (例: 94%)
summary = az.summary(trace, hdi_prob=0.94)
print("\nパラメータサマリー:")
print(summary)

# トレースプロットと事後分布のプロット
# トレースプロットはサンプリングの収束を確認するのに役立ちます
# 事後分布はパラメータの不確かさを表現します
print("\nトレースプロットと事後分布をプロット...")
az.plot_trace(trace)
plt.suptitle('Trace Plots', y=1.02) # 全体タイトル
plt.show()

az.plot_posterior(trace, hdi_prob=0.94)
plt.suptitle('Posterior Distributions', y=1.02)
plt.show()

# パラメータ間の相関図のプロット (特に多次元推定の場合に重要)
print("\nパラメータ間のペアワイズプロット...")
az.plot_pair(trace, kind='scatter', diag_kind='kde', marginals=True)
plt.suptitle('Pairwise Posterior Distributions', y=1.02)
plt.show()

# 収束診断 (R-hatとEffective Sample Size (ESS))
# R-hatが1に近いこと、ESSが十分大きいことが望ましい
print("\nR-hat 値:")
print(az.rhat(trace))
print("\nEffective Sample Size (ESS):")
print(az.ess(trace))


# --- 5. 拡張性に関するコメント ---
print("\n--- 拡張性について ---")
print("このコードは、要件定義の多くの側面に対応するための出発点となります。")
print("データ管理機能: observed_reactivity と delta_T をファイル読み込みから取得するように変更します。")
print("モデル組み込み機能: PyMC3モデル内の 'mu' の計算部分を外部関数として定義し、それを呼び出すように変更します。")
print("パラメータ設定・管理機能: 推定対象パラメータ (alpha_fuel, alpha_coolant) の名前、事前分布、範囲などをYAML/JSONファイルで定義し、コードがそれを読み込んでPyMC3モデルを動的に構築するようにします。")
print("Optunaによる最適化: PyMC3のMAP (Maximum A Posteriori) 推定機能や、モデルの対数尤度関数を利用して、Optunaで最適化問題を解くモジュールを追加します。")
print("非機能要件: エラーハンドリングやロギング機能を追加します。")
print("この基本構造を基盤として、要件定義に沿った本格的なツールへと発展させることが可能です。")
