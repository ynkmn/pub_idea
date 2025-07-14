from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern
import numpy as np

# パラメータと目的値を抽出
X = df[param_cols].values
y = df["value"].values

# GPR モデルの学習
kernel = Matern()
gpr = GaussianProcessRegressor(kernel=kernel, normalize_y=True)
gpr.fit(X, y)

# 予測と標準偏差
mu, sigma = gpr.predict(X, return_std=True)

# 平均と標準偏差を確認（例えば最適点周辺）
print(f"Mean around points: {mu}")
print(f"Standard deviation: {sigma}")