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


