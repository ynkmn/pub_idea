import pandas as pd
import numpy as np
import multiprocessing
import time
import os
from functools import partial

# --- 1. 各プロセスで実行される処理関数 ---
# この関数が並列処理の最小単位となります。
# 引数:
#   category (str): 処理対象のカテゴリ名
#   df (pd.DataFrame): 処理対象のデータ全体
# 戻り値:
#   np.array: 処理結果のNumPy配列
def worker(category, df):
    """
    指定されたカテゴリのデータを抽出し、特定の処理を行うワーカー関数。
    """
    # print(f"プロセス {os.getpid()} がカテゴリ '{category}' の処理を開始...")

    # dfから特定の条件（カテゴリ）でデータを抽出
    extracted_df = df[df['category'] == category].copy()

    # --- ここに重い処理を記述 ---
    # 例として、数値列の平均と標準偏差を計算し、新しい列として追加
    # 実際のユースケースに合わせて処理内容を変更してください。
    time.sleep(0.1) # 処理が重いことをシミュレート
    extracted_df['value1_mean'] = extracted_df['value1'].mean()
    extracted_df['value2_std'] = extracted_df['value2'].std()
    # --------------------------

    # 処理結果をNumPy配列として返す
    # カラムの順序を揃えておくと、後で結合しやすい
    return extracted_df[['id', 'category', 'value1', 'value2', 'value1_mean', 'value2_std']].to_numpy()


# --- 2. メイン処理 ---
# スクリプトとして実行された場合にのみ以下の処理を実行します。
# (multiprocessingを使用する際の定型句)
if __name__ == '__main__':
    print("処理を開始します...")
    start_time = time.time()

    # --- サンプルデータの作成 ---
    # 実際には、ここでCSVファイル等を読み込みます。
    # e.g., df = pd.read_csv('your_large_data.csv')
    num_records = 100000
    categories = [f'CAT_{i}' for i in range(20)]
    data = {
        'id': range(num_records),
        'category': np.random.choice(categories, num_records),
        'value1': np.random.rand(num_records) * 100,
        'value2': np.random.rand(num_records) * 50,
    }
    df = pd.DataFrame(data)
    print(f"サンプルデータを作成しました。レコード数: {len(df)}")


    # --- 並列処理の準備 ---
    # 処理対象となるカテゴリのユニークなリストを取得
    process_targets = df['category'].unique()

    # DataFrameをワーカー関数に渡すために、partialで引数を固定
    # これにより、pool.mapにカテゴリリストだけを渡せるようになります。
    # dfは各プロセスにコピーされます。
    process_func = partial(worker, df=df)

    # --- 並列処理の実行 ---
    # 使用するプロセス数を決定（CPUコア数 - 1 程度が一般的）
    # Noneを指定すると自動的にコア数になります。
    num_processes = multiprocessing.cpu_count() - 1 if multiprocessing.cpu_count() > 1 else 1
    print(f"{num_processes}個のプロセスで並列処理を実行します...")

    # プロセスプールを作成し、map関数で各カテゴリをワーカーに割り当て
    with multiprocessing.Pool(processes=num_processes) as pool:
        # pool.mapは、第2引数のリストの各要素を、第1引数の関数に渡して実行します。
        # 各プロセスからの戻り値（NumPy配列）がリストとして返されます。
        results_list = pool.map(process_func, process_targets)


    # --- 結果の結合とCSV出力 ---
    print("全プロセスの処理が完了。結果を結合します...")

    # 各プロセスから返されたNumPy配列のリストを縦に連結
    final_array = np.concatenate(results_list, axis=0)

    # 結合した配列をDataFrameに変換
    final_df = pd.DataFrame(final_array, columns=['id', 'category', 'value1', 'value2', 'value1_mean', 'value2_std'])

    # データ型を適切に変換
    final_df = final_df.astype({
        'id': 'int64',
        'value1': 'float64',
        'value2': 'float64',
        'value1_mean': 'float64',
        'value2_std': 'float64',
    })

    # CSVファイルとして保存
    output_path = 'processed_data_multiprocessing.csv'
    final_df.to_csv(output_path, index=False)

    end_time = time.time()
    print(f"処理が完了しました。結果は {output_path} に保存されました。")
    print(f"処理時間: {end_time - start_time:.2f} 秒")

