with open('sample.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    last_line = lines[-1].strip()
    print(last_line)




import matplotlib.pyplot as plt
import matplotlib.style as style

# 日本語表示のための設定
try:
    plt.rcParams['font.family'] = 'Meiryo'
except:
    plt.rcParams['font.family'] = 'sans-serif' # Meiryoがない環境向けのフォールバック

style.use('seaborn-v0_8-whitegrid')

# --- 1. ダミーデータの作成 ---
# 解析コードA (上端基準、z=0が上端)
z_A_upper = np.linspace(0, 10, 11)  # 0mから10mまで1mおき
T_A = 20 * np.exp(-z_A_upper / 5) + 10 * np.sin(z_A_upper) + 30  # 何らかの複雑な温度分布

# 解析コードB (上端基準、全高H_B = 10m)
total_height_B = 10.0
z_B_upper = np.array([0.5, 1.5, 3.0, 5.0, 7.5, 9.5]) # Aとは異なるメッシュ

# 解析コードC (下端基準、z=0が下端)
z_C_lower = np.linspace(0, 10, 51) # 0.2mおきの細かいメッシュ

# --- 2. クラスのインスタンス化とメソッドの実行 ---
# Aのデータで初期化
interpolator = ThermalProfileInterpolator(z_A_upper, T_A)

# ステップ1: AのデータからBのz座標における温度を補間
T_B_upper_interpolated = interpolator.interpolate_to_B_upper(z_B_upper)

# ステップ2: Bのデータを下端基準に変換し、Cのz座標で補間
T_C_lower_interpolated = interpolator.transform_B_and_interpolate_to_C_lower(total_height_B, z_C_lower)

# --- 3. 結果の可視化 ---
fig, ax = plt.subplots(figsize=(10, 8))

# 元データ (A) をプロット
ax.plot(T_A, z_A_upper, 'o-', c='blue', label='解析A: 元データ (上端基準)', markersize=8)

# Bで補間した点をプロット
ax.plot(T_B_upper_interpolated, z_B_upper, 's', c='red', label='解析B: 補間点 (上端基準)', markersize=10, alpha=0.8)

# Cで補間した結果をプロット (比較のため上端基準に変換してプロット)
z_C_upper_for_plot = total_height_B - z_C_lower
ax.plot(T_C_lower_interpolated, z_C_upper_for_plot, '--', c='green', label='解析C: 最終結果 (上端基準で表示)')

ax.set_xlabel('温度 T [°C]', fontsize=14)
ax.set_ylabel('上端基準 Z座標 [m]', fontsize=14)
ax.set_title('異なる解析コード間の温度プロファイル補間', fontsize=16)
ax.invert_yaxis()  # Z=0を上にする
ax.legend(fontsize=12)
ax.grid(True)

plt.show()




import numpy as np
from scipy.interpolate import interp1d

class ThermalProfileInterpolator:
    """
    数値解析コード間で、Z座標基準の変換と温度プロファイルの補間を行うクラス。

    一連の処理フロー:
    1. 解析コードAのデータ（上端基準）で初期化。
    2. 解析コードBのZ座標（上端基準）で温度を補間。
    3. 解析コードBのデータを下端基準に変換し、解析コードCのZ座標（下端基準）で温度を補間。

    Attributes:
        z_A_upper (np.ndarray): 解析コードAの上端基準Z座標。
        T_A (np.ndarray): 解析コードAの温度。
        interpolator_A_upper (scipy.interpolate.interp1d): Aのデータから作成した補間関数。
    """

    def __init__(self, z_A_upper: np.ndarray, T_A: np.ndarray):
        """
        クラスを初期化します。

        Args:
            z_A_upper (np.ndarray): 解析コードAの上端基準Z座標の配列。
            T_A (np.ndarray): 解析コードAの温度の配列。
        """
        # 補間を正しく行うため、入力データをZ座標でソートします。
        sort_indices = np.argsort(z_A_upper)
        self.z_A_upper = z_A_upper[sort_indices]
        self.T_A = T_A[sort_indices]

        # 解析コードAのデータ（上端基準）で線形補間関数を作成します。
        # bounds_error=False と fill_value="extrapolate" により、
        # 補間範囲外の点でも外挿して値を求めます。
        self.interpolator_A_upper = interp1d(
            self.z_A_upper,
            self.T_A,
            kind='linear',
            bounds_error=False,
            fill_value="extrapolate"
        )
        
        # 後続のメソッドで使用する変数を初期化しておきます。
        self._z_B_upper = None
        self._T_B_upper_interpolated = None

    def interpolate_to_B_upper(self, z_B_upper: np.ndarray) -> np.ndarray:
        """
        解析コードAのデータを使い、解析コードBの上端基準Z座標における温度を補間します。
        この結果はクラス内部に保存され、次のステップで使用されます。

        Args:
            z_B_upper (np.ndarray): 解析コードBの上端基準Z座標の配列。

        Returns:
            np.ndarray: BのZ座標で補間された温度の配列。
        """
        print("ステップ1: 解析Bの上端基準Z座標で温度を補間中...")
        self._z_B_upper = z_B_upper
        self._T_B_upper_interpolated = self.interpolator_A_upper(z_B_upper)
        print("=> 完了")
        return self._T_B_upper_interpolated

    def transform_B_and_interpolate_to_C_lower(self, total_height_B: float, z_C_lower: np.ndarray) -> np.ndarray:
        """
        Bの上端基準データを下端基準に変換し、そのデータを用いて
        解析コードCの下端基準Z座標で温度を補間します。

        Args:
            total_height_B (float): 解析コードBの解析領域の全高。
            z_C_lower (np.ndarray): 解析コードCの下端基準Z座標の配列。

        Returns:
            np.ndarray: CのZ座標で補間された温度の配列。

        Raises:
            ValueError: `interpolate_to_B_upper` メソッドが事前に呼び出されていない場合に発生します。
        """
        if self._z_B_upper is None or self._T_B_upper_interpolated is None:
            raise ValueError("エラー: 先に `interpolate_to_B_upper` メソッドを呼び出す必要があります。")

        print("ステップ2: 解析Bのデータを下端基準に変換し、解析Cの下端基準Z座標で補間中...")
        # Bの上端基準座標を下端基準に変換します。 (z_lower = H - z_upper)
        z_B_lower = total_height_B - self._z_B_upper

        # 下端基準に変換したBのデータを、Z座標でソートします。（補間のために必須）
        sort_indices = np.argsort(z_B_lower)
        z_B_lower_sorted = z_B_lower[sort_indices]
        T_B_lower_sorted = self._T_B_upper_interpolated[sort_indices]

        # ソートされたBの下端基準データで新しい補間関数を作成します。
        interpolator_B_lower = interp1d(
            z_B_lower_sorted,
            T_B_lower_sorted,
            kind='linear',
            bounds_error=False,
            fill_value="extrapolate"
        )

        # Cの下端基準Z座標で温度を補間します。
        T_C_lower_interpolated = interpolator_B_lower(z_C_lower)
        print("=> 完了")
        return T_C_lower_interpolated

