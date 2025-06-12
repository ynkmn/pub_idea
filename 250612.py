import pymc as pm
import numpy as np

# 観測データ（ダミー）
fuel_temp_obs = np.random.randn(100)
coolant_temp_obs = np.random.randn(100)
reactivity_obs = -5.0 * fuel_temp_obs - 3.0 * coolant_temp_obs + 0.1 + np.random.randn(100) * 0.5

# 追加したい既知の反応度（例：制御棒価値）
known_reactivity_offset = 0.1 # pcmなどの単位

with pm.Model() as reactor_model:
    # 1. パラメータの事前分布を定義
    fuel_temp_coef = pm.Normal("fuel_temp_coef", mu=-5.0, sigma=2.0)
    coolant_temp_coef = pm.Normal("coolant_temp_coef", mu=-3.0, sigma=2.0)

    # 2. 温度フィードバックによる反応度を計算
    reactivity_from_temp = fuel_temp_coef * fuel_temp_obs + coolant_temp_coef * coolant_temp_obs

    # 3. muの計算に既知の反応度を直接加える
    #    ここで単純に足し算するだけでOK
    mu = reactivity_from_temp + known_reactivity_offset

    # 4. 尤度関数を定義
    sigma = pm.HalfNormal("sigma", sigma=1.0)
    likelihood = pm.Normal(
        "likelihood",
        mu=mu,
        sigma=sigma,
        observed=reactivity_obs
    )

    # MCMCサンプリングの実行
    # idata = pm.sample()
