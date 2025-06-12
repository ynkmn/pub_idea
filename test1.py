“””
PyMC5を使用した原子炉温度係数の事後分布推定

このコードは、PyMC5のCustomDistを使用して、各サンプリング点で
解析コードを実行し、温度係数の事後分布を推定します。
“””

import numpy as np
import pandas as pd
import pymc as pm
import pytensor
import pytensor.tensor as pt
from pytensor.graph import Op, Apply
from pytensor.tensor.type import TensorType
import matplotlib.pyplot as plt
import arviz as az
from typing import Dict, Tuple, Optional, List
import logging

# ロギング設定

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

class ReactorAnalysisOp(Op):
“””
原子炉解析コードを実行するPyTensor操作

```
各温度係数のサンプリング点で解析コードを実行し、
対応する反応度を計算します。
"""

def __init__(self, time_data: np.ndarray, fuel_temp: np.ndarray, 
             coolant_temp: np.ndarray):
    """
    Args:
        time_data: 時間点の配列
        fuel_temp: 燃料温度の配列  
        coolant_temp: 冷却材温度の配列
    """
    self.time_data = time_data
    self.fuel_temp = fuel_temp
    self.coolant_temp = coolant_temp
    
def make_node(self, fuel_coeff, coolant_coeff):
    """PyTensorノードを作成"""
    fuel_coeff = pt.as_tensor_variable(fuel_coeff)
    coolant_coeff = pt.as_tensor_variable(coolant_coeff)
    
    # 出力の型を定義（反応度の時系列）
    output_type = TensorType(dtype='float64', shape=(len(self.time_data),))
    
    return Apply(self, [fuel_coeff, coolant_coeff], [output_type()])

def perform(self, node, inputs, outputs):
    """実際の計算を実行（ここで解析コードを呼び出す）"""
    fuel_coeff, coolant_coeff = inputs
    
    # 実際の解析コードを実行する部分
    # ここでは線形モデルの例を示すが、実際には複雑な解析コードを呼び出す
    reactivity = self._run_analysis_code(fuel_coeff, coolant_coeff)
    
    outputs[0][0] = reactivity

def _run_analysis_code(self, fuel_coeff: float, coolant_coeff: float) -> np.ndarray:
    """
    解析コードの実行（実装例）
    
    実際の用途では、ここで外部の原子炉解析コードを呼び出し、
    温度係数を使って反応度を再計算します。
    
    Args:
        fuel_coeff: 燃料温度係数
        coolant_coeff: 冷却材温度係数
        
    Returns:
        計算された反応度の時系列
    """
    # 簡単な線形モデルの例
    # 実際には、ここで以下のような処理を行います：
    # 1. 温度係数を解析コードに渡す
    # 2. 解析コードで温度分布を再計算
    # 3. 新しい温度分布から反応度を計算
    # 4. 結果を返す
    
    reactivity = fuel_coeff * self.fuel_temp + coolant_coeff * self.coolant_temp
    
    # より複雑な非線形効果を模擬
    # 実際の解析コードでは、温度係数の相互作用や
    # 空間依存性なども考慮されます
    reactivity += 0.1 * fuel_coeff * coolant_coeff * np.sin(self.time_data / 10)
    
    return reactivity.astype('float64')
```

class PyMCReactivityUQ:
“””
PyMC5を使用した原子炉反応度のベイズ推定クラス
“””

```
def __init__(self, time_data: np.ndarray, fuel_temp: np.ndarray, 
             coolant_temp: np.ndarray, observed_reactivity: np.ndarray):
    """
    Args:
        time_data: 時間点の配列
        fuel_temp: 燃料温度の配列
        coolant_temp: 冷却材温度の配列  
        observed_reactivity: 観測された反応度
    """
    self.time_data = time_data
    self.fuel_temp = fuel_temp
    self.coolant_temp = coolant_temp
    self.observed_reactivity = observed_reactivity
    
    # 解析コード実行用のOp
    self.analysis_op = ReactorAnalysisOp(time_data, fuel_temp, coolant_temp)
    
    self.model = None
    self.trace = None

def build_model(self, 
               fuel_coeff_prior: Tuple[float, float] = (-3.0, 1.0),
               coolant_coeff_prior: Tuple[float, float] = (-2.0, 1.0),
               sigma_prior: Tuple[float, float] = (0.1, 10.0)) -> pm.Model:
    """
    ベイズモデルを構築
    
    Args:
        fuel_coeff_prior: 燃料温度係数の事前分布 (mean, std)
        coolant_coeff_prior: 冷却材温度係数の事前分布 (mean, std)  
        sigma_prior: 観測誤差の事前分布 (lower, upper) - 一様分布
        
    Returns:
        構築されたPyMCモデル
    """
    with pm.Model() as model:
        # 事前分布の設定
        fuel_coeff = pm.Normal('fuel_temp_coeff', 
                             mu=fuel_coeff_prior[0], 
                             sigma=fuel_coeff_prior[1])
        
        coolant_coeff = pm.Normal('coolant_temp_coeff',
                                mu=coolant_coeff_prior[0],
                                sigma=coolant_coeff_prior[1])
        
        # 観測誤差の事前分布
        sigma = pm.Uniform('sigma', 
                          lower=sigma_prior[0], 
                          upper=sigma_prior[1])
        
        # CustomDistを使用して解析コードを実行
        def logp_func(observed_reactivity, fuel_coeff, coolant_coeff, sigma):
            """カスタム尤度関数"""
            # 解析コードを実行して予測反応度を計算
            predicted_reactivity = self.analysis_op(fuel_coeff, coolant_coeff)
            
            # 正規分布の対数尤度を計算
            logp = pm.math.sum(pm.logp(
                pm.Normal.dist(mu=predicted_reactivity, sigma=sigma),
                observed_reactivity
            ))
            return logp
        
        # CustomDistを使用
        likelihood = pm.CustomDist(
            'likelihood',
            fuel_coeff, coolant_coeff, sigma,
            logp=logp_func,
            observed=self.observed_reactivity,
            signature='(),(),()->(n)'  # スカラー3つ → ベクトル1つ
        )
    
    self.model = model
    return model

def sample_posterior(self, 
                    draws: int = 2000,
                    tune: int = 1000, 
                    chains: int = 4,
                    cores: int = 2,
                    **kwargs) -> az.InferenceData:
    """
    事後分布のサンプリング
    
    Args:
        draws: サンプル数
        tune: チューニング数
        chains: チェーン数
        cores: 並列実行のコア数
        **kwargs: その他のpm.sample引数
        
    Returns:
        サンプリング結果
    """
    if self.model is None:
        raise ValueError("モデルが構築されていません。build_model()を先に実行してください。")
    
    logger.info(f"事後分布のサンプリングを開始...")
    logger.info(f"draws={draws}, tune={tune}, chains={chains}")
    
    with self.model:
        # サンプリング実行
        self.trace = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            cores=cores,
            **kwargs
        )
    
    logger.info("サンプリング完了")
    return self.trace

def plot_posterior(self, var_names: Optional[List[str]] = None):
    """事後分布の可視化"""
    if self.trace is None:
        raise ValueError("サンプリングが実行されていません。")
    
    if var_names is None:
        var_names = ['fuel_temp_coeff', 'coolant_temp_coeff', 'sigma']
    
    # トレースプロット
    az.plot_trace(self.trace, var_names=var_names)
    plt.tight_layout()
    plt.show()
    
    # 事後分布プロット
    az.plot_posterior(self.trace, var_names=var_names)
    plt.tight_layout()
    plt.show()

def plot_predictions(self, n_samples: int = 100):
    """予測結果の可視化"""
    if self.trace is None:
        raise ValueError("サンプリングが実行されていません。")
    
    # サンプルを抽出
    posterior_samples = self.trace.posterior
    
    # ランダムにサンプルを選択
    n_chains, n_draws = posterior_samples.sizes['chain'], posterior_samples.sizes['draw']
    selected_indices = np.random.choice(n_draws * n_chains, n_samples, replace=False)
    
    plt.figure(figsize=(12, 8))
    
    # 観測データをプロット
    plt.plot(self.time_data, self.observed_reactivity, 'ko', 
            label='観測データ', alpha=0.7, markersize=4)
    
    # 事後予測サンプルをプロット
    predictions = []
    for i, idx in enumerate(selected_indices):
        chain_idx = idx // n_draws
        draw_idx = idx % n_draws
        
        fuel_coeff = float(posterior_samples['fuel_temp_coeff'][chain_idx, draw_idx])
        coolant_coeff = float(posterior_samples['coolant_temp_coeff'][chain_idx, draw_idx])
        
        # 予測反応度を計算
        predicted = self.analysis_op._run_analysis_code(fuel_coeff, coolant_coeff)
        predictions.append(predicted)
        
        if i < 50:  # 最初の50サンプルのみプロット
            plt.plot(self.time_data, predicted, 'r-', alpha=0.1)
    
    # 予測の統計量を計算
    predictions = np.array(predictions)
    pred_mean = np.mean(predictions, axis=0)
    pred_std = np.std(predictions, axis=0)
    
    # 平均と信頼区間をプロット
    plt.plot(self.time_data, pred_mean, 'r-', label='予測平均', linewidth=2)
    plt.fill_between(self.time_data, 
                    pred_mean - 2*pred_std, 
                    pred_mean + 2*pred_std,
                    alpha=0.3, color='red', label='95%信頼区間')
    
    plt.xlabel('時間 [s]')
    plt.ylabel('反応度 [pcm]')
    plt.title('事後予測分布')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def summary(self) -> pd.DataFrame:
    """推定結果のサマリー"""
    if self.trace is None:
        raise ValueError("サンプリングが実行されていません。")
    
    summary_df = az.summary(self.trace, 
                           var_names=['fuel_temp_coeff', 'coolant_temp_coeff', 'sigma'])
    return summary_df

def export_results(self, filepath: str):
    """結果をファイルに保存"""
    if self.trace is None:
        raise ValueError("サンプリングが実行されていません。")
    
    # サマリーをCSVで保存
    summary_df = self.summary()
    summary_df.to_csv(filepath.replace('.csv', '_summary.csv'))
    
    # トレースをNetCDFで保存
    self.trace.to_netcdf(filepath.replace('.csv', '_trace.nc'))
    
    logger.info(f"結果を保存しました: {filepath}")
```

def example_usage():
“”“使用例”””
# 1. 仮想データの生成
time_data = np.linspace(0, 100, 101)
fuel_temp = 300 + 50 * (1 - np.exp(-time_data / 20))
coolant_temp = 290 + 30 * (1 - np.exp(-time_data / 30))

```
# 真のパラメータ
true_fuel_coeff = -2.5
true_coolant_coeff = -1.8
true_sigma = 5.0

# 真の反応度（非線形効果を含む）
true_reactivity = (true_fuel_coeff * fuel_temp + 
                  true_coolant_coeff * coolant_temp + 
                  0.1 * true_fuel_coeff * true_coolant_coeff * np.sin(time_data / 10))

# 観測データ（ノイズ付き）
np.random.seed(42)
observed_reactivity = true_reactivity + np.random.normal(0, true_sigma, len(time_data))

# 2. PyMCモデルの構築と実行
uq_tool = PyMCReactivityUQ(time_data, fuel_temp, coolant_temp, observed_reactivity)

# モデル構築
model = uq_tool.build_model(
    fuel_coeff_prior=(-3.0, 1.0),
    coolant_coeff_prior=(-2.0, 1.0),
    sigma_prior=(0.1, 20.0)
)

# サンプリング実行
trace = uq_tool.sample_posterior(
    draws=1000,  # 例なので少なめに設定
    tune=500,
    chains=2,
    cores=1
)

# 3. 結果の表示
print("=== 推定結果サマリー ===")
print(uq_tool.summary())

print(f"\n=== 真値との比較 ===")
print(f"燃料温度係数: 真値={true_fuel_coeff}, 推定値={trace.posterior['fuel_temp_coeff'].mean().values:.3f}")
print(f"冷却材温度係数: 真値={true_coolant_coeff}, 推定値={trace.posterior['coolant_temp_coeff'].mean().values:.3f}")
print(f"観測誤差: 真値={true_sigma}, 推定値={trace.posterior['sigma'].mean().values:.3f}")

# 4. 結果の可視化
uq_tool.plot_posterior()
uq_tool.plot_predictions()

# 5. 結果の保存
uq_tool.export_results("pymc_reactivity_results.csv")
```

if **name** == “**main**”:
example_usage()