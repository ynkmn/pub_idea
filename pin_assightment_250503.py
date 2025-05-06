#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ピン代表点割り当て・番号付与ツール

高速炉燃料集合体（六角格子）において、各ピンに代表点を割り当てる
ためのピン番号付与と値の割り当てを自動化するツール。
"""

import math
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.colors import Normalize
from abc import ABC, abstractmethod
import os


class Pin:
    """ピンを表すクラス"""
    
    def __init__(self, ring=None, position=None, coordinates=None):
        self.id = None  # ピン番号（螺旋状）
        self.ring = ring  # リング番号
        self.position = position  # リング内位置
        self.coordinates = coordinates  # (x, y)座標
        self.value = None  # 割り当て値
        self.subchannel_id = None  # サブチャンネル方式のID
        
    def __str__(self):
        return f"Pin(id={self.id}, ring={self.ring}, pos={self.position}, coord={self.coordinates}, value={self.value}, subchannel_id={self.subchannel_id})"


class HexagonalGrid:
    """六角格子を表すクラス"""
    
    def __init__(self, rings, pitch):
        """
        六角格子の初期化
        
        Args:
            rings (int): リング数
            pitch (float): ピン間距離（ピッチ）
        """
        self.rings = rings
        self.pitch = pitch
        self.pins = []
        self.total_pins = sum(1 + 6 * i for i in range(rings))
        
    # def generate_pins(self):
    #     """中心から螺旋状にピンを生成する"""
    #     # 中心ピン
    #     center_pin = Pin(ring=0, position=0, coordinates=(0, 0))
    #     self.pins.append(center_pin)
        
    #     # 周辺リング
    #     # for ring in range(1, self.rings):
    #     for ring in range(1, self.rings+1):
    #         pins_in_ring = 6 * ring
    #         for pos in range(pins_in_ring):
    #             angle = 2 * math.pi * pos / pins_in_ring
    #             # 30度回転させて、六角形の頂点が上に来るようにする
    #             angle += math.pi / 6
                
    #             # 六角格子の座標計算（リング番号と角度から）
    #             x = self.pitch * ring * math.cos(angle)
    #             y = self.pitch * ring * math.sin(angle)
                
    #             pin = Pin(ring=ring, position=pos, coordinates=(x, y))
    #             self.pins.append(pin)
    def generate_pins(self):
        # 中心ピン
        center_pin = Pin(ring=0, position=0, coordinates=(0, 0))
        self.pins.append(center_pin)

        # 周辺リング
        for ring in range(1, self.rings+1):  # 1からself.ringsまで
            for side in range(6):  # 6辺
                for step in range(ring):
                    # 六角格子の軸座標
                    # 各辺の開始点
                    if side == 0:
                        q, r_ = ring, -step
                    elif side == 1:
                        q, r_ = ring-step, -ring
                    elif side == 2:
                        q, r_ = -step, -ring+step
                    elif side == 3:
                        q, r_ = -ring, step
                    elif side == 4:
                        q, r_ = -ring+step, ring
                    elif side == 5:
                        q, r_ = step, ring-step

                    # x, y座標に変換
                    x = self.pitch * (q + r_/2)
                    y = self.pitch * (math.sqrt(3)/2) * self.pitch * r_
                    pin = Pin(ring=ring, position=None, coordinates=(x, y))
                    self.pins.append(pin)

    def assign_spiral_ids(self):
        """螺旋状にIDを割り当て"""
        # ピンを中心から外側へ、各リング内は角度順に並べ替え
        sorted_pins = sorted(self.pins, key=lambda p: (p.ring, p.position))
        
        # 螺旋状に番号を割り当て
        for i, pin in enumerate(sorted_pins):
            pin.id = i
    
    def convert_to_subchannel_ids(self):
        """サブチャンネル方式（上段左端から右へ、上から下へ）に変換"""
        # 各ピンのy座標でグループ化して行を特定
        pins_by_y = {}
        for pin in self.pins:
            # 浮動小数点の誤差を避けるため、小数点以下の桁を丸める
            y_rounded = round(pin.coordinates[1], 6)
            if y_rounded not in pins_by_y:
                pins_by_y[y_rounded] = []
            pins_by_y[y_rounded].append(pin)
        
        # y座標の値で降順にソート（上から下へ）
        sorted_y_values = sorted(pins_by_y.keys(), reverse=True)
        
        # 各行内でx座標でソート（左から右へ）
        subchannel_id = 1
        for y in sorted_y_values:
            row_pins = pins_by_y[y]
            # x座標でソート
            row_pins.sort(key=lambda p: p.coordinates[0])
            
            # サブチャンネルIDを割り当て
            for pin in row_pins:
                pin.subchannel_id = subchannel_id
                subchannel_id += 1
    
    def get_pin_by_spiral_id(self, spiral_id):
        """螺旋IDからピンを取得"""
        for pin in self.pins:
            if pin.id == spiral_id:
                return pin
        return None
    
    def get_pin_by_subchannel_id(self, subchannel_id):
        """サブチャンネルIDからピンを取得"""
        for pin in self.pins:
            if pin.subchannel_id == subchannel_id:
                return pin
        return None


class InterpolationStrategy(ABC):
    """補間方法の基底クラス"""
    
    @abstractmethod
    def interpolate(self, pins, input_values):
        """
        各ピンに値を割り当てる
        
        Args:
            pins (list): Pinオブジェクトのリスト
            input_values (dict): 補間に必要な入力値
        """
        pass


class ThreePointInterpolation(InterpolationStrategy):
    """3点補間による値の割り当て"""
    
    def interpolate(self, pins, input_values):
        """
        中心ピーク値、外側ピーク値、外側最小値による3点補間
        
        Args:
            pins (list): Pinオブジェクトのリスト
            input_values (dict): {
                'center_peak': float, # 中心ピークの値
                'outer_peak': float,  # 外側ピークの値
                'outer_min': float    # 外側最小値
            }
        """
        center_peak = input_values.get('center_peak', 100.0)
        outer_peak = input_values.get('outer_peak', 80.0)
        outer_min = input_values.get('outer_min', 60.0)
        
        max_ring = max(pin.ring for pin in pins)
        
        for pin in pins:
            # 中心ピン
            if pin.ring == 0:
                pin.value = center_peak
            else:
                # 外側ピンは角度に応じて値を変える
                # 0度方向（基準方向）でピーク値、180度方向で最小値
                angle = math.atan2(pin.coordinates[1], pin.coordinates[0])
                # -π〜πの範囲を0〜2πに変換
                if angle < 0:
                    angle += 2 * math.pi
                
                # リングごとの重み（中心からの距離に応じた補間）
                ring_ratio = pin.ring / max_ring
                
                # 角度に応じた値の変化（コサイン関数で滑らかに変化）
                angle_factor = (1 + math.cos(angle)) / 2  # 0〜1の範囲
                
                # 最終的な値の計算
                value_range = outer_peak - outer_min
                pin.value = outer_min + value_range * angle_factor
                
                # 中心からの値の変化を反映（線形補間）
                center_to_outer_diff = pin.value - center_peak
                pin.value = center_peak + center_to_outer_diff * ring_ratio


class SevenPointInterpolation(InterpolationStrategy):
    """7点補間による値の割り当て"""
    
    def interpolate(self, pins, input_values):
        """
        中心ピーク値と六角頂点位置のピーク値（6点）による7点補間
        
        Args:
            pins (list): Pinオブジェクトのリスト
            input_values (dict): {
                'center_peak': float,    # 中心ピークの値
                'vertex_values': list    # 六角形の頂点位置の値（6点）
            }
        """
        center_peak = input_values.get('center_peak', 100.0)
        vertex_values = input_values.get('vertex_values', [80.0] * 6)
        
        # 頂点値が6つでない場合は調整
        if len(vertex_values) < 6:
            vertex_values.extend([80.0] * (6 - len(vertex_values)))
        elif len(vertex_values) > 6:
            vertex_values = vertex_values[:6]
        
        max_ring = max(pin.ring for pin in pins)
        
        for pin in pins:
            # 中心ピン
            if pin.ring == 0:
                pin.value = center_peak
            else:
                # 六角形の60度ごとの頂点方向（0, 60, 120, 180, 240, 300度）
                angle = math.atan2(pin.coordinates[1], pin.coordinates[0])
                # -π〜πの範囲を0〜2πに変換
                if angle < 0:
                    angle += 2 * math.pi
                
                # 角度を0〜360度に変換
                angle_deg = math.degrees(angle)
                
                # 最も近い2つの頂点を特定
                sector = int(angle_deg / 60)
                next_sector = (sector + 1) % 6
                
                # 2つの頂点間での角度の位置（0〜1）
                sector_pos = (angle_deg - sector * 60) / 60
                
                # 2点間の値を線形補間
                interpolated_value = vertex_values[sector] * (1 - sector_pos) + vertex_values[next_sector] * sector_pos
                
                # リングごとの重み（中心からの距離に応じた補間）
                ring_ratio = pin.ring / max_ring
                
                # 中心から頂点への値の変化を反映（線形補間）
                center_to_vertex_diff = interpolated_value - center_peak
                pin.value = center_peak + center_to_vertex_diff * ring_ratio


class OutputBuilder(ABC):
    """出力形式の基底クラス"""
    
    def __init__(self):
        self.output = None
    
    @abstractmethod
    def build_data(self, pins):
        """
        ピンデータを出力形式に変換
        
        Args:
            pins (list): Pinオブジェクトのリスト
            
        Returns:
            出力形式に応じたデータ
        """
        pass
    
    def get_output(self):
        """出力データを取得"""
        return self.output


class CSVOutputBuilder(OutputBuilder):
    """CSV形式の出力ビルダー"""
    
    def build_data(self, pins, filename="pin_data.csv"):
        """
        CSVフォーマットでデータを構築
        
        Args:
            pins (list): Pinオブジェクトのリスト
            filename (str): 出力ファイル名
            
        Returns:
            str: 出力ファイルパス
        """
        data = []
        for pin in pins:
            data.append({
                'spiral_id': pin.id,
                'subchannel_id': pin.subchannel_id,
                'ring': pin.ring,
                'position': pin.position,
                'x': pin.coordinates[0],
                'y': pin.coordinates[1],
                'value': pin.value
            })
        
        # CSVに書き込み
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['spiral_id', 'subchannel_id', 'ring', 'position', 'x', 'y', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        self.output = filename
        return filename


class ExcelOutputBuilder(OutputBuilder):
    """Excel形式の出力ビルダー"""
    
    def build_data(self, pins, filename="pin_data.xlsx"):
        """
        Excelフォーマットでデータを構築
        
        Args:
            pins (list): Pinオブジェクトのリスト
            filename (str): 出力ファイル名
            
        Returns:
            str: 出力ファイルパス
        """
        data = []
        for pin in pins:
            data.append({
                'spiral_id': pin.id,
                'subchannel_id': pin.subchannel_id,
                'ring': pin.ring,
                'position': pin.position,
                'x': pin.coordinates[0],
                'y': pin.coordinates[1],
                'value': pin.value
            })
        
        # DataFrameに変換
        df = pd.DataFrame(data)
        
        # Excelに書き込み
        df.to_excel(filename, index=False)
        
        self.output = filename
        return filename


class PinAssignmentTool:
    """ピン代表点割り当て・番号付与ツール"""
    
    def __init__(self, rings=5, pitch=1.0, total_pins=None):
        """
        ツールの初期化
        
        Args:
            rings (int): リング数
            pitch (float): ピン間距離（ピッチ）
            total_pins (int, optional): ピン総数（指定された場合はリング数より優先）
        """
        # ピン総数からリング数を計算
        if total_pins is not None:
            rings = self.calculate_rings_from_total_pins(total_pins)
            
        self.grid = HexagonalGrid(rings, pitch)
        self.interpolator = None
        self.output_builder = None
    
    @staticmethod
    def calculate_rings_from_total_pins(total_pins):
        """
        ピン総数からリング数を計算
        
        Args:
            total_pins (int): ピン総数
            
        Returns:
            int: リング数
        """
        if total_pins <= 0:
            return 0
            
        # 六角格子のリングrにおけるピン数は 1 + 3r(r+1)
        # 累積ピン数を計算し、total_pins以上になる最小のリング数を見つける
        rings = 0
        cumulative_pins = 0
        
        while cumulative_pins < total_pins:
            cumulative_pins = sum(1 + 6 * i for i in range(rings + 1))
            if cumulative_pins >= total_pins:
                break
            rings += 1
            
        return rings
    
    def set_interpolation_strategy(self, strategy):
        """補間方法の設定"""
        self.interpolator = strategy
    
    def set_output_builder(self, builder):
        """出力ビルダーの設定"""
        self.output_builder = builder
    
    def generate_grid(self):
        """グリッドの生成とピン番号付与"""
        self.grid.generate_pins()
        self.grid.assign_spiral_ids()
        return self.grid
    
    def convert_to_subchannel_ids(self):
        """サブチャンネル方式IDへの変換"""
        self.grid.convert_to_subchannel_ids()
    
    def assign_values(self, input_values):
        """代表点値の割り当て"""
        if not self.interpolator:
            raise ValueError("補間方法が設定されていません")
        self.interpolator.interpolate(self.grid.pins, input_values)
    
    def generate_output(self, filename=None):
        """出力の生成"""
        if not self.output_builder:
            raise ValueError("出力ビルダーが設定されていません")
        
        if filename:
            return self.output_builder.build_data(self.grid.pins, filename)
        else:
            return self.output_builder.build_data(self.grid.pins)
    
    def get_spiral_to_subchannel_mapping(self, filename="id_mapping.csv"):
        """
        螺旋IDからサブチャンネルIDへのマッピングを出力
        
        Args:
            filename (str): 出力ファイル名
            
        Returns:
            str: 出力ファイルパス
        """
        mapping = []
        for pin in self.grid.pins:
            mapping.append({
                'spiral_id': pin.id,
                'subchannel_id': pin.subchannel_id
            })
        
        # CSVに書き込み
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['spiral_id', 'subchannel_id']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in mapping:
                writer.writerow(row)
        
        return filename
    
    def visualize(self, show_values=True, color_map='viridis', filename=None, title=None):
        """
        ピン配置と代表点値の可視化
        
        Args:
            show_values (bool): 値を表示するかどうか
            color_map (str): カラーマップ名
            filename (str): 保存するファイル名（Noneの場合は保存しない）
            title (str): グラフのタイトル
            
        Returns:
            matplotlib.figure.Figure: 作成した図
        """
        # ピンの値が設定されているか確認
        has_values = all(pin.value is not None for pin in self.grid.pins)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 六角形のピンを描画
        for pin in self.grid.pins:
            x, y = pin.coordinates
            
            # 六角形の描画（ピンを表現）
            hex_radius = self.grid.pitch / 2 * 0.9  # 隣接ピンと重ならないよう少し小さめに
            hexagon = RegularPolygon((x, y), numVertices=6, radius=hex_radius,
                                    orientation=0, alpha=0.7, edgecolor='k')
            
            # 値に応じて色を設定
            if has_values and show_values:
                values = [pin.value for pin in self.grid.pins]
                norm = Normalize(vmin=min(values), vmax=max(values))
                hexagon.set_facecolor(plt.cm.get_cmap(color_map)(norm(pin.value)))
            else:
                hexagon.set_facecolor('lightgray')
            
            ax.add_patch(hexagon)
            
            # IDの表示
            if show_values and has_values:
                # 値を表示
                ax.text(x, y, f"{pin.value:.1f}", ha='center', va='center', fontsize=8)
            else:
                # IDを表示
                ax.text(x, y, f"S:{pin.id}\nC:{pin.subchannel_id}", ha='center', va='center', fontsize=8)
        
        # カラーバーの追加（値がある場合のみ）
        if has_values and show_values:
            values = [pin.value for pin in self.grid.pins]
            sm = plt.cm.ScalarMappable(cmap=color_map, norm=Normalize(vmin=min(values), vmax=max(values)))
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax)
            cbar.set_label('Value')
        
        # グラフの設定
        ax.set_aspect('equal')
        ax.autoscale_view()
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        
        if title:
            ax.set_title(title)
        else:
            if show_values and has_values:
                ax.set_title('ピン配置と代表点値')
            else:
                ax.set_title('ピン配置とID')
        
        # ファイルに保存
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        plt.tight_layout()
        return fig


def main():
    """メイン関数"""
    print("六角格子ピン代表点割り当て・番号付与ツール")
    
    # 入力方法の選択
    input_method = input("入力方法を選択してください（1: ピン総数, 2: リング数）[1]: ") or "1"
    
    rings = 5  # デフォルト値
    total_pins = None
    
    if input_method == "1":
        # ピン総数からの入力
        try:
            total_pins = int(input("ピン総数を入力してください: "))
            if total_pins <= 0:
                print("ピン総数は正の整数を入力してください。デフォルト値（リング数5）を使用します。")
                total_pins = None
                rings = 5
            else:
                # ピン総数からリング数を計算（表示用）
                rings = PinAssignmentTool.calculate_rings_from_total_pins(total_pins)
                print(f"指定されたピン総数 {total_pins} に対応するリング数: {rings}")
                
                # 計算されたリング数でのピン総数を表示
                actual_pins = sum(1 + 6 * i for i in range(rings))
                if actual_pins > total_pins:
                    print(f"注意: 六角格子の構造上、実際のピン総数は {actual_pins} となります")
        except ValueError:
            print("入力が無効です。デフォルト値（リング数5）を使用します。")
            total_pins = None
            rings = 5
    else:
        # リング数からの入力
        try:
            rings = int(input("リング数を入力してください（例: 5）: "))
            if rings <= 0:
                print("リング数は正の整数を入力してください。デフォルト値の5を使用します。")
                rings = 5
        except ValueError:
            print("入力が無効です。デフォルト値の5を使用します。")
            rings = 5
    
    try:
        pitch = float(input("ピッチを入力してください（例: 1.0）: "))
        if pitch <= 0:
            print("ピッチは正の数を入力してください。デフォルト値の1.0を使用します。")
            pitch = 1.0
    except ValueError:
        print("入力が無効です。デフォルト値の1.0を使用します。")
        pitch = 1.0
    
    # 補間方法の選択
    interpolation_choice = input("補間方法を選択してください（1: 3点補間, 2: 7点補間）[1]: ") or "1"
    
    # ツールの初期化
    tool = PinAssignmentTool(rings=rings, pitch=pitch, total_pins=total_pins)
    
    # グリッドの生成とピン番号付与
    grid = tool.generate_grid()
    
    # サブチャンネル方式IDへの変換
    tool.convert_to_subchannel_ids()
    
    # 補間方法の設定と代表点値の割り当て
    if interpolation_choice == "1":
        # 3点補間
        try:
            center_peak = float(input("中心ピーク値を入力してください [100.0]: ") or "100.0")
            outer_peak = float(input("外側ピーク値を入力してください [80.0]: ") or "80.0")
            outer_min = float(input("外側最小値を入力してください [60.0]: ") or "60.0")
        except ValueError:
            print("入力が無効です。デフォルト値を使用します。")
            center_peak = 100.0
            outer_peak = 80.0
            outer_min = 60.0
        
        input_values = {
            "center_peak": center_peak,
            "outer_peak": outer_peak,
            "outer_min": outer_min
        }
        
        interpolator = ThreePointInterpolation()
    else:
        # 7点補間
        try:
            center_peak = float(input("中心ピーク値を入力してください [100.0]: ") or "100.0")
            print("六角形の頂点位置の値（6点）を入力してください:")
            vertex_values = []
            for i in range(6):
                val = float(input(f"頂点{i+1}の値 [80.0]: ") or "80.0")
                vertex_values.append(val)
        except ValueError:
            print("入力が無効です。デフォルト値を使用します。")
            center_peak = 100.0
            vertex_values = [80.0] * 6
        
        input_values = {
            "center_peak": center_peak,
            "vertex_values": vertex_values
        }
        
        interpolator = SevenPointInterpolation()
    
    tool.set_interpolation_strategy(interpolator)
    tool.assign_values(input_values)
    
    # 出力形式の選択
    output_format = input("出力形式を選択してください（1: CSV, 2: Excel）[1]: ") or "1"
    
    # 出力ディレクトリの作成
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    if output_format == "1":
        # CSV出力
        csv_builder = CSVOutputBuilder()
        tool.set_output_builder(csv_builder)
        csv_file = tool.generate_output(os.path.join(output_dir, "pin_data.csv"))
        print(f"CSV出力が完了しました: {csv_file}")
    else:
        # Excel出力
        excel_builder = ExcelOutputBuilder()
        tool.set_output_builder(excel_builder)
        excel_file = tool.generate_output(os.path.join(output_dir, "pin_data.xlsx"))
        print(f"Excel出力が完了しました: {excel_file}")
    
    # マッピング情報の出力
    mapping_file = tool.get_spiral_to_subchannel_mapping(os.path.join(output_dir, "id_mapping.csv"))
    print(f"ID対応表が出力されました: {mapping_file}")
    
    # 可視化
    visualize = input("ピン配置を可視化しますか？（y/n）[y]: ") or "y"
    if visualize.lower() == "y":
        show_values = input("代表点値を表示しますか？（y/n）[y]: ") or "y"
        show_values = show_values.lower() == "y"
        
        # IDマップの可視化
        id_fig = tool.visualize(show_values=False, filename=os.path.join(output_dir, "pin_id_map.png"), 
                               title="ピン配置とID（S:螺旋ID, C:サブチャンネルID）")
        
        if show_values:
            # 値の可視化
            val_fig = tool.visualize(show_values=True, filename=os.path.join(output_dir, "pin_value_map.png"),
                                   title="ピン配置と代表点値")
        
        print(f"可視化画像が出力されました: {output_dir}ディレクトリ")
        
        # 表示
        plt.show()


if __name__ == "__main__":
    main()