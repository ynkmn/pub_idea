import pymc3 as pm
import arviz as az
# ... （既存のimport文）

class ReactivityUQ:
    # ... (既存のメソッドはそのまま) 

    def __init__(self,
                 reactivity_model: ReactivityModel,
                 error_metric: ErrorMetric = None): # 
        self.reactivity_model = reactivity_model # 
        self.error_metric = error_metric if error_metric is not None else MSE() # 
        self.parameters_for_bayes = [] # ベイズ推定用のパラメータ定義
        self.trace = None # MCMCサンプリング結果を格納
        # ... (既存の初期化) 

    def add_parameter_for_bayes(self, name: str, prior_type: str, prior_params: dict, initial_value: Optional[float] = None):
        """ベイズ推定するパラメータと事前分布の情報を追加する"""
        # name: パラメータ名
        # prior_type: 'normal', 'uniform' などのPyMC3で利用可能な分布名
        # prior_params: 分布のパラメータ (例: {'mu': 0, 'sd': 1} for Normal)
        # initial_value: MCMCの初期値 (オプション)
        self.parameters_for_bayes.append({
            'name': name,
            'prior_type': prior_type,
            'prior_params': prior_params,
            'initial_value': initial_value
        })
        logger.info(f"ベイズ推定用パラメータ '{name}' を追加しました (事前分布: {prior_type}, パラメータ: {prior_params})")


    def run_bayesian_estimation(self,
                                time_data: np.ndarray,
                                observed_reactivity: np.ndarray,
                                draws: int = 2000,
                                tune: int = 1000,
                                chains: int = 2,
                                cores: int = 1,
                                target_accept: float = 0.8,
                                **model_inputs) -> pm.backends.base.MultiTrace:
        """
        PyMC3を使用してベイズ推定を実行し、事後分布のサンプルを取得する

        Args:
            time_data: 時間点の配列 
            observed_reactivity: 観測された反応度の配列 
            draws: MCMCサンプリングの描画数
            tune: チューニング（バーンイン）のステップ数
            chains: MCMCチェーンの数
            cores: 使用するCPUコア数
            target_accept: NUTSサンプラーの目標受容率
            **model_inputs: モデルへの追加入力（温度データなど）

        Returns:
            PyMC3のMultiTraceオブジェクト (事後分布のサンプル)
        """
        if not self.parameters_for_bayes:
            raise ValueError("ベイズ推定用のパラメータが設定されていません。add_parameter_for_bayes()を使用してください。")

        with pm.Model() as reactor_model:
            # 1. パラメータの事前分布を定義
            params_vars = {}
            for p_info in self.parameters_for_bayes:
                if p_info['prior_type'].lower() == 'normal':
                    params_vars[p_info['name']] = pm.Normal(p_info['name'], **p_info['prior_params'])
                elif p_info['prior_type'].lower() == 'uniform':
                    params_vars[p_info['name']] = pm.Uniform(p_info['name'], **p_info['prior_params'])
                # 他の事前分布タイプも追加可能
                else:
                    raise ValueError(f"未対応の事前分布タイプ: {p_info['prior_type']}")

            # 2. モデル予測
            #    (self.reactivity_model.calculate_reactivity をPyMC3のテンソル演算で扱えるようにする必要がある場合がある)
            #    簡単のため、ここでは calculate_reactivity が Theano/Aesara の演算を直接受け付けない前提で、
            #    pm.Deterministic や pm.Potential を使うか、モデル構造を工夫する必要がある。
            #    ここでは、単純化のため、モデル関数が直接呼び出せると仮定します。
            #    実際には、Theanoのラッパー関数を介すか、モデルをPyMC3内で再構築する必要があるかもしれません。

            # --- PyMC3内でモデル計算を行うためのラッパー関数 (例) ---
            # @pm.deterministic
            # def pymc3_reactivity_model(t, **current_params_vars_and_model_inputs):
            #     # current_params_vars_and_model_inputs から必要なパラメータと入力を取り出す
            #     # self.reactivity_model.calculate_reactivity を呼び出す
            #     # この部分は self.reactivity_model の実装に依存します
            #     param_dict_for_model = {name: current_params_vars_and_model_inputs[name] for name in params_vars.keys()}
            #     other_inputs_for_model = {k: v for k, v in current_params_vars_and_model_inputs.items() if k not in params_vars}
            #     return self.reactivity_model.calculate_reactivity(t, param_dict_for_model, **other_inputs_for_model)

            # # 上記のラッパーを使う場合
            # all_model_inputs_for_pymc = {**params_vars, **model_inputs} # パラメータと固定入力をマージ
            # predicted_reactivity_mean = pymc3_reactivity_model(time_data, **all_model_inputs_for_pymc)

            # --- Theano/Aesara 互換のモデル関数を直接定義する (推奨される場合が多い) ---
            # 線形モデルの例 
            if isinstance(self.reactivity_model, LinearReactivityModel): # 
                reactivity_calc = 0.0
                if 'fuel_temp_coef' in params_vars and 'fuel_temp' in model_inputs:
                    reactivity_calc += params_vars['fuel_temp_coef'] * model_inputs['fuel_temp'] # 
                if 'coolant_temp_coef' in params_vars and 'coolant_temp' in model_inputs:
                    reactivity_calc += params_vars['coolant_temp_coef'] * model_inputs['coolant_temp'] # 
                # 他の項も同様に追加
                predicted_reactivity_mean = reactivity_calc
            else:
                # 他のモデルタイプの場合は、それに応じてPyMC3内で計算を記述
                raise NotImplementedError("この反応度モデルタイプはPyMC3の自動組み込みに対応していません。")


            # 3. 観測誤差の事前分布
            sigma = pm.HalfNormal('sigma', sigma=10) # 例: 観測誤差の標準偏差の事前分布

            # 4. 尤度
            likelihood = pm.Normal('observed_reactivity',
                                   mu=predicted_reactivity_mean,
                                   sigma=sigma,
                                   observed=observed_reactivity) # 

            # 5. MCMCサンプリング
            logger.info("MCMCサンプリングを開始します...")
            start_time = time.time()
            self.trace = pm.sample(draws=draws,
                                   tune=tune,
                                   chains=chains,
                                   cores=cores,
                                   target_accept=target_accept,
                                   return_inferencedata=True) # InferenceDataオブジェクトで取得するとarvizと連携しやすい
            elapsed_time = time.time() - start_time
            logger.info(f"MCMCサンプリング完了（{elapsed_time:.2f}秒）")

        return self.trace

    def plot_posterior(self, trace=None, var_names: Optional[List[str]] = None):
        """事後分布をプロットする (arvizを使用)"""
        if trace is None:
            trace = self.trace
        if trace is None:
            raise ValueError("サンプリング結果(trace)がありません。run_bayesian_estimation()を先に実行してください。")

        if var_names is None:
            var_names = [p['name'] for p in self.parameters_for_bayes] + ['sigma'] # sigmaも表示する場合

        az.plot_trace(trace, var_names=var_names)
        plt.tight_layout()
        plt.show()

        az.plot_posterior(trace, var_names=var_names)
        plt.tight_layout()
        plt.show()

        if len(var_names) > 1:
            az.plot_pair(trace, var_names=var_names, kind='kde', divergences=True)
            plt.tight_layout()
            plt.show()

    def get_posterior_summary(self, trace=None, var_names: Optional[List[str]] = None, stat_funcs=None, fmt="wide"):
        """事後分布の要約統計量を取得する (arvizを使用)"""
        if trace is None:
            trace = self.trace
        if trace is None:
            raise ValueError("サンプリング結果(trace)がありません。run_bayesian_estimation()を先に実行してください。")

        if var_names is None:
            var_names = [p['name'] for p in self.parameters_for_bayes] + ['sigma']

        return az.summary(trace, var_names=var_names, stat_funcs=stat_funcs, fmt=fmt)

# --- 使用例の変更 ---
def example_usage_bayesian():
    # ... (データの準備は example_usage と同様) 
    time_data = np.linspace(0, 100, 101) # 
    fuel_temp = 300 + 50 * (1 - np.exp(-time_data / 20)) # 
    coolant_temp = 290 + 30 * (1 - np.exp(-time_data / 30)) # 

    true_fuel_temp_coef = -2.0 # 
    true_coolant_temp_coef = -1.5 # 
    true_reactivity = true_fuel_temp_coef * fuel_temp + true_coolant_temp_coef * coolant_temp # 
    observed_reactivity = true_reactivity + np.random.normal(0, 5, len(time_data)) # ノイズ少し小さめ

    # UQツールの初期化
    reactivity_model = LinearReactivityModel() # 
    uq_tool = ReactivityUQ(reactivity_model) # 

    # ベイズ推定用パラメータの追加
    uq_tool.add_parameter_for_bayes("fuel_temp_coef", "normal", {'mu': -2.5, 'sd': 1.0}) # の範囲を参考に事前分布を設定
    uq_tool.add_parameter_for_bayes("coolant_temp_coef", "normal", {'mu': -1.0, 'sd': 1.0}) # 

    # ベイズ推定の実行
    trace = uq_tool.run_bayesian_estimation(
        time_data,
        observed_reactivity, # 
        fuel_temp=fuel_temp, # 
        coolant_temp=coolant_temp, # 
        draws=3000, tune=1500, chains=2, cores=1 # 適宜調整
    )

    # 結果の表示
    summary = uq_tool.get_posterior_summary(trace)
    print("事後分布の要約統計量:")
    print(summary)

    print(f"\n真のパラメータ: fuel_temp_coef={true_fuel_temp_coef}, coolant_temp_coef={true_coolant_temp_coef}") # 

    # 事後分布のプロット
    uq_tool.plot_posterior(trace)

if __name__ == "__main__":
    # example_usage() # 既存の最適化ベースの例
    example_usage_bayesian() # ベイズ推定の例

