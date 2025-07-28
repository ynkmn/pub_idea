import os
import shutil
import yaml

class ParametricStudy:
    """
    パラメータ解析のためのスタディを管理するクラス。

    Attributes:
        template_dir (str): 解析テンプレートのディレクトリパス。
        output_base_dir (str): 解析ケースを出力するベースディレクトリパス。
    """
    def __init__(self, template_dir: str, output_base_dir: str):
        """
        ParametricStudyのインスタンスを初期化します。

        Args:
            template_dir (str): テンプレートディレクトリのパス。
            output_base_dir (str): 出力ベースディレクトリのパス。
        """
        self.template_dir = template_dir
        self.output_base_dir = output_base_dir
        
        # 出力ベースディレクトリが存在しない場合は作成
        os.makedirs(self.output_base_dir, exist_ok=True)
        print(f"出力先ベースディレクトリ: '{self.output_base_dir}'")

    def run_study(self, study_parameters: list[dict], yaml_filename: str = 'params.yaml'):
        """
        パラメータリストに基づいてパラメトリックスタディを実行します。

        各パラメータセットに対して、以下の処理を行います。
        1. テンプレートディレクトリをコピーして、新しいケースディレクトリを作成します。
        2. ケースディレクトリ内にパラメータを記述したYAMLファイルを作成します。

        Args:
            study_parameters (list[dict]): 各ケースのパラメータを含む辞書のリスト。
            yaml_filename (str, optional): 生成するYAMLファイルの名前。デフォルトは 'params.yaml'。
        """
        if not os.path.isdir(self.template_dir):
            print(f"❌ エラー: テンプレートディレクトリ '{self.template_dir}' が見つかりません。")
            return

        print(f"🚀 {len(study_parameters)} ケースのスタディを開始します...")
        for i, params in enumerate(study_parameters):
            case_name = f"case_{i+1:03d}"
            case_dir = os.path.join(self.output_base_dir, case_name)

            try:
                # 1. テンプレートディレクトリをコピー
                if os.path.exists(case_dir):
                    shutil.rmtree(case_dir) # 既に存在する場合は上書き
                shutil.copytree(self.template_dir, case_dir)

                # 2. パラメータをYAMLファイルに書き込み
                yaml_path = os.path.join(case_dir, yaml_filename)
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(params, f, default_flow_style=False, allow_unicode=True)
                
                print(f"  ✅ ケース '{case_name}' を作成しました。 path: {case_dir}")

            except Exception as e:
                print(f"  ❌ ケース '{case_name}' の作成中にエラーが発生しました: {e}")
        
        print("🎉 パラメトリックスタディのセットアップが完了しました。")


# --- メインの実行部分 ---
if __name__ == '__main__':
    
    # 1. パラメータ設定
    # 解析したいパラメータのリストを定義 (10ケース)
    study_params_list = [
        {'learning_rate': 0.01, 'batch_size': 32, 'optimizer': 'Adam'},
        {'learning_rate': 0.02, 'batch_size': 32, 'optimizer': 'Adam'},
        {'learning_rate': 0.03, 'batch_size': 32, 'optimizer': 'Adam'},
        {'learning_rate': 0.01, 'batch_size': 64, 'optimizer': 'Adam'},
        {'learning_rate': 0.02, 'batch_size': 64, 'optimizer': 'Adam'},
        {'learning_rate': 0.03, 'batch_size': 64, 'optimizer': 'Adam'},
        {'learning_rate': 0.01, 'batch_size': 32, 'optimizer': 'SGD'},
        {'learning_rate': 0.02, 'batch_size': 32, 'optimizer': 'SGD'},
        {'learning_rate': 0.01, 'batch_size': 64, 'optimizer': 'SGD'},
        {'learning_rate': 0.02, 'batch_size': 64, 'optimizer': 'SGD'},
    ]

    # 2. パラメトリックスタディの実行
    
    # クラスのインスタンス化
    # - template_dir: コピー元のテンプレートディレクトリ
    # - output_base_dir: 解析ケースを作成する場所
    study = ParametricStudy(template_dir='template_case', output_base_dir='results')

    # スタディの実行
    study.run_study(study_parameters=study_params_list, yaml_filename='config.yaml')
