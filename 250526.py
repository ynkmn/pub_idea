

import re

s = "data(1,2,3,4)"
result = re.sub(r'(data|value)\(([\d,]+)\)', lambda m: f"{m.group(1)}_" + m.group(2).replace(',', '_'), s)
print(result)  # 出力: data_1_2_3_4

s2 = "value(5,6,7)"
result2 = re.sub(r'(data|value)\(([\d,]+)\)', lambda m: f"{m.group(1)}_" + m.group(2).replace(',', '_'), s2)
print(result2)  # 出力: value_5_6_7



import re

s = "data(1,2,3,4)"
result = re.sub(r'data\(([\d,]+)\)', lambda m: "data_" + m.group(1).replace(',', '_'), s)
print(result)  # 出力: data_1_2_3_4



from abc import ABC, abstractmethod
from typing import Dict, List, Any, Type
import yaml
import json
import csv


# Strategy パターン: 変換ロジックのインターフェース
class Converter(ABC):
    @abstractmethod
    def convert(self, data: Dict) -> Any:
        """入力データを変換して返す抽象メソッド"""
        pass


# 単純な1対1の変換を行うConverter
class SimpleConverter(Converter):
    def __init__(self, params: Dict = None):
        self.params = params or {}
    
    def convert(self, data: Dict) -> Any:
        """単一の入力変数を変換"""
        # 入力変数の値を取得
        value = data.get(list(data.keys())[0])
        
        # パラメータに基づいて変換処理を実行
        if self.params.get("scaling_factor"):
            value = value * self.params["scaling_factor"]
        
        return value


# 単位変換を行うConverter
class UnitConverter(Converter):
    def __init__(self, params: Dict = None):
        self.params = params or {}
        self.unit_from = self.params.get("from", "")
        self.unit_to = self.params.get("to", "")
        self.conversion_factor = self.params.get("factor", 1.0)
    
    def convert(self, data: Dict) -> Any:
        """単位変換を行う"""
        value = data.get(list(data.keys())[0])
        return value * self.conversion_factor


# Composite パターン: 複数入力変数を扱うConverter
class CompositeConverter(Converter):
    def __init__(self, params: Dict = None):
        self.params = params or {}
    
    def convert(self, data: Dict) -> Any:
        """
        複数の入力変数を組み合わせて変換
        パラメータの'formula'キーに数式を定義
        例: "x + y" や "x * 2 + y / 3" など
        """
        formula = self.params.get("formula", "")
        locals_dict = data.copy()
        
        try:
            result = eval(formula, {"__builtins__": {}}, locals_dict)
            return result
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {str(e)}")


# 集約処理を行うConverter
class AggregationConverter(Converter):
    def __init__(self, params: Dict = None):
        self.params = params or {}
        self.method = self.params.get("method", "sum")
    
    def convert(self, data: Dict) -> Any:
        """
        複数の入力値を集約処理
        methodパラメータで集約方法を指定（sum, avg, max, minなど）
        """
        values = list(data.values())
        
        if self.method == "sum":
            return sum(values)
        elif self.method == "avg":
            return sum(values) / len(values)
        elif self.method == "max":
            return max(values)
        elif self.method == "min":
            return min(values)
        else:
            raise ValueError(f"Unknown aggregation method: {self.method}")


# Factory Method パターン: Converterオブジェクトを生成
class ConverterFactory:
    def __init__(self):
        self._converters = {}
        
        # デフォルトの変換ロジックを登録
        self.register_converter("simple", SimpleConverter)
        self.register_converter("unit", UnitConverter)
        self.register_converter("composite", CompositeConverter)
        self.register_converter("aggregation", AggregationConverter)
    
    def register_converter(self, converter_type: str, converter_class: Type[Converter]):
        """新しい変換ロジッククラスを登録"""
        self._converters[converter_type] = converter_class
    
    def create_converter(self, converter_type: str, params: Dict = None) -> Converter:
        """指定された型とパラメータで変換ロジックを生成"""
        converter_class = self._converters.get(converter_type)
        if not converter_class:
            raise ValueError(f"Unknown converter type: {converter_type}")
        
        return converter_class(params)


# マッピング情報を保持するクラス
class Mapping:
    def __init__(self, source_code: str, target_code: str, source_variables: List[str],
                 target_variable: str, converter_type: str, params: Dict = None):
        self.source_code = source_code
        self.target_code = target_code
        self.source_variables = source_variables
        self.target_variable = target_variable
        self.converter_type = converter_type
        self.params = params or {}


# Adapter パターン: 異なる形式のマッピング定義を内部表現に変換
class MappingAdapter:
    @staticmethod
    def from_yaml(file_path: str) -> List[Mapping]:
        """YAMLファイルからマッピング定義を読み込む"""
        with open(file_path, 'r') as f:
            mappings_data = yaml.safe_load(f)
        
        return MappingAdapter.from_dict(mappings_data)
    
    @staticmethod
    def from_json(file_path: str) -> List[Mapping]:
        """JSONファイルからマッピング定義を読み込む"""
        with open(file_path, 'r') as f:
            mappings_data = json.load(f)
        
        return MappingAdapter.from_dict(mappings_data)
    
    @staticmethod
    def from_csv(file_path: str) -> List[Mapping]:
        """CSVファイルからマッピング定義を読み込む"""
        mappings = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_variables = row['source_variables'].split(',')
                params_str = row.get('params', '{}')
                try:
                    params = json.loads(params_str)
                except json.JSONDecodeError:
                    params = {}
                
                mappings.append(Mapping(
                    source_code=row['source_code'],
                    target_code=row['target_code'],
                    source_variables=source_variables,
                    target_variable=row['target_variable'],
                    converter_type=row['converter_type'],
                    params=params
                ))
        
        return mappings
    
    @staticmethod
    def from_dict(mappings_data: Dict) -> List[Mapping]:
        """辞書型からマッピング定義を生成"""
        mappings = []
        for mapping_item in mappings_data.get('mappings', []):
            mappings.append(Mapping(
                source_code=mapping_item['source_code'],
                target_code=mapping_item['target_code'],
                source_variables=mapping_item['source_variables'],
                target_variable=mapping_item['target_variable'],
                converter_type=mapping_item['converter_type'],
                params=mapping_item.get('params', {})
            ))
        
        return mappings


# マッピング情報を管理するクラス
class MappingManager:
    def __init__(self):
        self.mappings = []
    
    def add_mapping(self, mapping: Mapping):
        """マッピングを追加"""
        self.mappings.append(mapping)
    
    def add_mappings(self, mappings: List[Mapping]):
        """複数のマッピングをまとめて追加"""
        self.mappings.extend(mappings)
    
    def get_mappings(self, source_code: str, target_code: str) -> List[Mapping]:
        """指定したソースコードとターゲットコード間のマッピングを取得"""
        return [m for m in self.mappings 
                if m.source_code == source_code and m.target_code == target_code]


# Builder パターン: データ変換処理全体を構築
class DataConverter:
    def __init__(self):
        self.mapping_manager = MappingManager()
        self.converter_factory = ConverterFactory()
    
    def load_mappings_from_file(self, file_path: str, file_format: str = None):
        """ファイルからマッピング定義を読み込む"""
        if file_format is None:
            # ファイル拡張子から形式を推測
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                file_format = 'yaml'
            elif file_path.endswith('.json'):
                file_format = 'json'
            elif file_path.endswith('.csv'):
                file_format = 'csv'
            else:
                raise ValueError("Unknown file format. Please specify explicitly.")
        
        if file_format == 'yaml':
            mappings = MappingAdapter.from_yaml(file_path)
        elif file_format == 'json':
            mappings = MappingAdapter.from_json(file_path)
        elif file_format == 'csv':
            mappings = MappingAdapter.from_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        self.mapping_manager.add_mappings(mappings)
    
    def load_mappings_from_dict(self, mappings_dict: Dict):
        """辞書型からマッピング定義を読み込む"""
        mappings = MappingAdapter.from_dict(mappings_dict)
        self.mapping_manager.add_mappings(mappings)
    
    def convert(self, source_data: Dict, source_code: str, target_code: str) -> Dict:
        """
        ソースデータを変換
        source_data: 変換元データ（辞書型）
        source_code: 変換元コード識別子
        target_code: 変換先コード識別子
        """
        # 該当するマッピングを取得
        mappings = self.mapping_manager.get_mappings(source_code, target_code)
        if not mappings:
            raise ValueError(f"No mapping found for {source_code} -> {target_code}")
        
        # 変換結果を格納する辞書
        result = {}
        
        # 各マッピングに従って変換処理を実行
        for mapping in mappings:
            # 入力変数の値を取得
            input_data = {}
            for var_name in mapping.source_variables:
                if var_name not in source_data:
                    raise ValueError(
                        f"Source variable '{var_name}' not found in input data")
                input_data[var_name] = source_data[var_name]
            
            # 変換ロジックを生成
            converter = self.converter_factory.create_converter(
                mapping.converter_type, mapping.params)
            
            # 変換を実行
            result[mapping.target_variable] = converter.convert(input_data)
        
        return result


# 使用例
def usage_example():
    # マッピング定義
    mappings_dict = {
        "mappings": [
            {
                "source_code": "code_a",
                "target_code": "code_b",
                "source_variables": ["temperature_c"],
                "target_variable": "temperature_f",
                "converter_type": "unit",
                "params": {
                    "from": "celsius",
                    "to": "fahrenheit",
                    "factor": 1.8,
                    "offset": 32
                }
            },
            {
                "source_code": "code_a",
                "target_code": "code_b",
                "source_variables": ["x", "y"],
                "target_variable": "z",
                "converter_type": "composite",
                "params": {
                    "formula": "x**2 + y**2"
                }
            }
        ]
    }
    
    # データ変換器を初期化
    converter = DataConverter()
    
    # マッピング定義を読み込み
    converter.load_mappings_from_dict(mappings_dict)
    
    # 入力データ
    input_data = {
        "temperature_c": 25,
        "x": 3,
        "y": 4
    }
    
    # 変換を実行
    result = converter.convert(input_data, "code_a", "code_b")
    print(result)  # {'temperature_f': 45.0, 'z': 25}


if __name__ == "__main__":
    usage_example()




mappings:
  # 単純な1対1の変換
  - source_code: "analysis_code_a"
    target_code: "analysis_code_b"
    source_variables: ["temperature_celsius"]
    target_variable: "temperature_fahrenheit"
    converter_type: "unit"
    params:
      from: "celsius"
      to: "fahrenheit"
      factor: 1.8
      offset: 32
  
  # スケーリング変換
  - source_code: "analysis_code_a"
    target_code: "analysis_code_b"
    source_variables: ["density_kg_m3"]
    target_variable: "density_g_cm3"
    converter_type: "unit"
    params:
      factor: 0.001
  
  # 多対1の変換（複合計算）
  - source_code: "analysis_code_a"
    target_code: "analysis_code_c"
    source_variables: ["length", "width", "height"]
    target_variable: "volume"
    converter_type: "composite"
    params:
      formula: "length * width * height"
  
  # 多対1の変換（集約）
  - source_code: "analysis_code_b"
    target_code: "analysis_code_c"
    source_variables: ["temperature_1", "temperature_2", "temperature_3"]
    target_variable: "average_temperature"
    converter_type: "aggregation"
    params:
      method: "avg"
  
  # 座標系変換の例
  - source_code: "analysis_code_a"
    target_code: "analysis_code_d"
    source_variables: ["x_cartesian", "y_cartesian"]
    target_variable: "r_polar"
    converter_type: "composite"
    params:
      formula: "(x_cartesian**2 + y_cartesian**2)**0.5"
  
  - source_code: "analysis_code_a"
    target_code: "analysis_code_d"
    source_variables: ["x_cartesian", "y_cartesian"]
    target_variable: "theta_polar"
    converter_type: "composite"
    params:
      formula: "math.atan2(y_cartesian, x_cartesian)"
      imports: ["math"]