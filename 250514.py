    def visualize_axial_distribution(self, z_positions, filename=None, title=None):
        """
        ピン配置と軸方向分布の可視化

        Args:
            z_positions (list): 軸方向の位置リスト
            filename (str): 保存するファイル名（Noneの場合は保存しない）
            title (str): グラフのタイトル

        Returns:
            matplotlib.figure.Figure: 作成した図
        """

        fig, ax = plt.subplots(figsize=(10, 8))

        # 六角形のピンを描画
        for pin in self.grid.pins:
            x, y = pin.coordinates
            hex_radius = self.grid.pitch / 2 * 0.9
            hexagon = RegularPolygon((x, y), numVertices=6, radius=hex_radius,
                                    orientation=0, alpha=0.7, edgecolor='k')
            ax.add_patch(hexagon)

            # 軸方向分布をプロット
            if pin.value is not None and isinstance(pin.value, list):
                # プロット位置を調整
                text_x = x + self.grid.pitch * 0.6
                text_y = y - self.grid.pitch * 0.6
                ax.text(text_x, text_y, f"S:{pin.id}", ha='left', va='top', fontsize=6)  # IDを小さく表示
                for i, z in enumerate(z_positions):
                    val = pin.value[i]
                    ax.plot([x, x + self.grid.pitch * 0.5], [y - i * self.grid.pitch * 0.1, y - i * self.grid.pitch * 0.1], marker='o', markersize=2, color='r')
                    ax.text(x + self.grid.pitch * 0.55, y - i * self.grid.pitch * 0.1, f"{val:.1f}", ha='left', va='center', fontsize=6)

        # グラフの設定
        ax.set_aspect('equal')
        ax.autoscale_view()
        ax.set_xlabel('X')
        ax.set_ylabel('Y')

        if title:
            ax.set_title(title)
        else:
            ax.set_title('ピン配置と軸方向分布')

        # ファイルに保存
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig


    # 可視化
    visualize = input("ピン配置を可視化しますか？（y/n）[y]: ") or "y"
    if visualize.lower() == "y":
        show_values = input("代表点値を表示しますか？（y/n）[y]: ") or "y"
        show_values = show_values.lower() == "y"

        # IDマップの可視化
        id_fig = tool.visualize(show_values=False, filename=os.path.join(output_dir, "pin_id_map.png"),
                               title="ピン配置とID（S:螺旋ID, C:サブチャンネルID）")

        if show_values:
            if value_assignment_choice == "1" and interpolation_choice == "2":
                # 軸方向分布の可視化
                tool.visualize_axial_distribution(input_values["z_positions"], filename=os.path.join(output_dir, "pin_axial_distribution.png"),
                                                title="ピン配置と軸方向分布")
            else:
                # 値の可視化
                val_fig = tool.visualize(show_values=True, filename=os.path.join(output_dir, "pin_value_map.png"),
                                       title="ピン配置と代表点値")

        print(f"可視化画像が出力されました: {output_dir}ディレクトリ")

        # 表示
        plt.show()




class SevenPointInterpolation(InterpolationStrategy):
    """7点補間による値の割り当て (軸方向分布対応)"""

    def interpolate(self, pins, input_values):
        """
        中心の値と六角形の頂点位置の値（6点）による7点補間。
        各ピンの軸方向分布を考慮。

        Args:
            pins (list): Pinオブジェクトのリスト
            input_values (dict): {
                'center_values': list,    # 中心の軸方向分布の値のリスト
                'vertex_values': list    # 六角形の頂点位置の値のリスト (各頂点も軸方向分布)
                'z_positions': list      # 軸方向の位置リスト (例: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
            }
        """
        center_values = input_values.get('center_values', [100.0])  # デフォルトは一律の値
        vertex_values = input_values.get('vertex_values', [[80.0] * len(center_values)] * 6) # デフォルトは一律の値
        z_positions = input_values.get('z_positions', [0.0])  # 軸方向の位置

        if len(vertex_values) != 6 or any(len(v) != len(center_values) for v in vertex_values):
            raise ValueError("頂点データの次元が不正です")

        max_ring = max(pin.ring for pin in pins)
        num_z = len(z_positions)

        for pin in pins:
            pin.value = []  # 軸方向の値を格納するリストとして初期化

            for z_index in range(num_z):
                # 中心の値
                if pin.ring == 0:
                    pin.value.append(center_values[z_index])
                else:
                    # 角度計算
                    angle = math.atan2(pin.coordinates[1], pin.coordinates[0])
                    if angle < 0:
                        angle += 2 * math.pi

                    angle_deg = math.degrees(angle)
                    sector = int(angle_deg / 60)
                    next_sector = (sector + 1) % 6
                    sector_pos = (angle_deg - sector * 60) / 60

                    # 頂点値の補間
                    interpolated_value = vertex_values[sector][z_index] * (1 - sector_pos) + vertex_values[next_sector][z_index] * sector_pos

                    # リング方向の補間
                    ring_ratio = pin.ring / max_ring
                    center_to_vertex_diff = interpolated_value - center_values[z_index]
                    pin.value.append(center_values[z_index] + center_to_vertex_diff * ring_ratio)



def main():
    # ... (省略)

    # 補間方法の設定と代表点値の割り当て
    if interpolation_choice == "1":
        # 3点補間 (変更なし)
        # ...
        pass
    else:
        # 7点補間 (軸方向分布対応)
        try:
            center_values = []
            num_z = int(input("軸方向の分割数を入力してください: "))
            print("中心の軸方向分布の値を入力してください:")
            for i in range(num_z):
                val = float(input(f"  z[{i+1}]の値: ") or "100.0")
                center_values.append(val)

            vertex_values = [[] for _ in range(6)]
            print("六角形の頂点位置の軸方向分布の値を入力してください (各頂点{num_z}点):")
            for j in range(6):
                print(f"頂点{j+1}:")
                for i in range(num_z):
                    val = float(input(f"  z[{i+1}]の値 [80.0]: ") or "80.0")
                    vertex_values[j].append(val)

            z_positions = []
            print("軸方向の位置を入力してください:")
            for i in range(num_z):
                z = float(input(f"  z[{i+1}]の位置: ") or f"{i / (num_z - 1):.1f}")
                z_positions.append(z)

        except ValueError:
            print("入力が無効です。デフォルト値を使用します。")
            center_values = [100.0] * num_z
            vertex_values = [[80.0] * num_z] * 6
            z_positions = [i / (num_z - 1) for i in range(num_z)]

        input_values = {
            "center_values": center_values,
            "vertex_values": vertex_values,
            "z_positions": z_positions
        }

        interpolator = SevenPointInterpolation()

    tool.set_interpolation_strategy(interpolator)
    tool.assign_values(input_values)
    
    
        def assign_values_from_spiral_id(self, spiral_id_values):
        """
        螺旋IDをキーとしてピンに値を割り当てる

        Args:
            spiral_id_values (dict): 螺旋IDをキー、値を値とする辞書
        """
        for spiral_id, value in spiral_id_values.items():
            pin = self.grid.get_pin_by_spiral_id(spiral_id)
            if pin:
                pin.value = value
            else:
                print(f"警告: 螺旋ID {spiral_id} に対応するピンが見つかりません。")


def main():
    # ... (省略)

    # 値の割り当て方法の選択
    value_assignment_choice = input("値の割り当て方法を選択してください（1: 補間, 2: 螺旋IDから割り当て）[1]: ") or "1"

    if value_assignment_choice == "1":
        # 補間処理
        # ... (既存の補間処理)
        pass
    elif value_assignment_choice == "2":
        # 螺旋IDから割り当て
        try:
            num_pins = len(tool.grid.pins)
            spiral_id_values = {}
            print(f"各ピンの値を螺旋ID順に入力してください (ピン総数: {num_pins}):")
            for i in range(num_pins):
                value = float(input(f"  螺旋ID {i} の値: "))
                spiral_id_values[i] = value
        except ValueError:
            print("入力が無効です。値の割り当てをスキップします。")
            spiral_id_values = {}

        tool.assign_values_from_spiral_id(spiral_id_values)
    else:
        print("無効な選択です。値の割り当てをスキップします。")

    # ... (出力処理など)


