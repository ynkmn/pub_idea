import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any

# ------------------------------------------------------------------------------
# 1. 抽象基底クラス (共通インターフェースの定義)
# ------------------------------------------------------------------------------
class InputGenerator(ABC):
    """
    解析入力ファイルジェネレータの抽象基底クラス。
    すべての具象ジェネレーターはこのクラスを継承する必要があります。
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def generate(self, params: Dict[str, Any], step: str) -> None:
        """
        設計パラメータと計算ステップに基づいて入力ファイルを生成します。

        Args:
            params (Dict[str, Any]): 設計パラメータが格納された辞書。
            step (str): 計算ステップ ('initial', 'restart'など)。
        """
        pass

# ------------------------------------------------------------------------------
# 2. 具象ジェネレータークラス (各解析コードごとの実装)
# ------------------------------------------------------------------------------
class StructureInputGenerator(InputGenerator):
    """構造解析の入力ファイルを生成するクラス。"""
    def generate(self, params: Dict[str, Any], step: str) -> None:
        print(f"[{self.__class__.__name__}] generating for step: '{step}'")
        
        if step == 'initial':
            # 初期計算用の入力ファイルを作成
            content = f"""
*INITIAL_ANALYSIS
*MATERIAL, DENSITY={params['material']['density']}
*GEOMETRY, THICKNESS={params['geometry']['thickness']}
"""
            filepath = self.output_dir / "structure_initial.inp"
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  -> Created: {filepath}")

        elif step == 'restart':
            # リスタート計算用の入力ファイルを作成
            content = f"""
*RESTART_ANALYSIS
*LOAD_CASE, FORCE={params['load']['force']}
"""
            filepath = self.output_dir / "structure_restart.inp"
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  -> Created: {filepath}")
            
        else:
            print(f"  -> Warning: Unknown step '{step}' for {self.__class__.__name__}")

class FluidInputGenerator(InputGenerator):
    """流体解析の入力ファイルを生成するクラス。"""
    def generate(self, params: Dict[str, Any], step: str) -> None:
        print(f"[{self.__class__.__name__}] generating for step: '{step}'")
        
        # この解析では初期計算のみファイルを生成すると仮定
        if step == 'initial':
            content = f"""
# Fluid Analysis Input
# VISCOSITY: {params['fluid']['viscosity']}
# VELOCITY: {params['boundary']['inlet_velocity']}
"""
            filepath = self.output_dir / "fluid.inp"
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  -> Created: {filepath}")
        
        # リスタートでは何もしない
        else:
            print(f"  -> No file generated for step '{step}' in {self.__class__.__name__}")


# ------------------------------------------------------------------------------
# 3. 連携管理クラス (全体のワークフローを管理)
# ------------------------------------------------------------------------------
class AnalysisOrchestrator:
    """
    連成解析のワークフロー全体を管理するクラス。
    """
    def __init__(self, json_params: str):
        """
        Args:
            json_params (str): ベイズ最適化から渡されるJSON形式の設計パラメータ文字列。
        """
        self.params = json.loads(json_params)
        self.generators: List[InputGenerator] = []

    def add_generator(self, generator: InputGenerator) -> None:
        """
        この連成解析で使用する入力ファイルジェネレーターを追加します。
        
        Args:
            generator (InputGenerator): InputGeneratorを継承したクラスのインスタンス。
        """
        self.generators.append(generator)
        print(f"Added generator: {generator.__class__.__name__}")

    def prepare_inputs(self, step: str) -> None:
        """
        指定された計算ステップの入力ファイルをすべて生成します。

        Args:
            step (str): 計算ステップ ('initial', 'restart'など)。
        """
        print(f"\n--- Preparing inputs for step: '{step}' ---")
        if not self.generators:
            print("Warning: No generators have been added.")
            return
            
        for generator in self.generators:
            generator.generate(self.params, step)
        print("--- Preparation complete ---")

# ------------------------------------------------------------------------------
# 実行例
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # 1. ベイズ最適化システムからJSON形式のパラメータが渡されたと仮定
    design_params_json = """
    {
        "geometry": {
            "thickness": 1.5,
            "width": 10.0
        },
        "material": {
            "density": 7.85e-9
        },
        "load": {
            "force": 500
        },
        "fluid": {
            "viscosity": 1.0e-3
        },
        "boundary": {
            "inlet_velocity": 2.5
        }
    }
    """

    # 2. 連携管理クラスを初期化
    orchestrator = AnalysisOrchestrator(design_params_json)

    # 3. この解析で使用するジェネレーターを追加
    #    (異なる出力ディレクトリを指定することも可能)
    orchestrator.add_generator(StructureInputGenerator(output_dir="output/structure"))
    orchestrator.add_generator(FluidInputGenerator(output_dir="output/fluid"))

    # 4. 連成解析の計算ステップに応じて入力ファイルを生成
    
    # 初期計算の入力ファイルを生成
    orchestrator.prepare_inputs(step='initial')
    
    # リスタート計算の入力ファイルを生成
    orchestrator.prepare_inputs(step='restart')

    # 未知のステップを試す
    orchestrator.prepare_inputs(step='final_post')
