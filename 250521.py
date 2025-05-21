import os
import shutil
import glob

def recursive_copy_selected_files(source_dir, dest_dir, target_files_patterns):
    """
    指定されたフォルダから、指定されたファイルパターンに一致するファイルを再帰的にコピーします。

    Args:
        source_dir (str): コピー元のディレクトリパス。
        dest_dir (str): コピー先のディレクトリパス。
        target_files_patterns (list): コピーしたいファイル名のパターン（例: ['*.txt', 'image.jpg']）のリスト。
                                      globパターンも使用できます。
    """
    if not os.path.exists(source_dir):
        print(f"エラー: ソースディレクトリ '{source_dir}' が存在しません。")
        return

    os.makedirs(dest_dir, exist_ok=True) # 宛先ディレクトリが存在しない場合は作成

    print(f"'{source_dir}' から '{dest_dir}' へファイルを探してコピーします...")
    print(f"対象ファイルパターン: {target_files_patterns}")

    copied_count = 0
    skipped_count = 0

    for root, _, files in os.walk(source_dir):
        for file in files:
            # 各ファイルパターンに対してチェック
            should_copy = False
            for pattern in target_files_patterns:
                # glob.fnmatch.fnmatch は Python 3.6 にないため、glob.glob を使用
                # ただし、os.walk と組み合わせるため、ここでは単純なパターンマッチング
                # より高度なパターンマッチングが必要な場合は fnmatch モジュールを使用
                if glob.fnmatch.fnmatch(file, pattern):
                    should_copy = True
                    break

            if should_copy:
                source_filepath = os.path.join(root, file)
                # ソースディレクトリからの相対パスを取得
                relative_path = os.path.relpath(source_filepath, source_dir)
                dest_filepath = os.path.join(dest_dir, relative_path)

                # 宛先ディレクトリを再帰的に作成
                os.makedirs(os.path.dirname(dest_filepath), exist_ok=True)

                if os.path.exists(dest_filepath):
                    # ファイルが存在し、かつソースファイルの更新時刻が宛先ファイルより新しい場合のみコピー
                    # この簡易的なチェックはrsyncの--updateに相当
                    if os.path.getmtime(source_filepath) > os.path.getmtime(dest_filepath):
                        print(f"更新: '{source_filepath}' -> '{dest_filepath}'")
                        shutil.copy2(source_filepath, dest_filepath)
                        copied_count += 1
                    else:
                        print(f"スキップ (新しい): '{dest_filepath}'")
                        skipped_count += 1
                else:
                    print(f"コピー: '{source_filepath}' -> '{dest_filepath}'")
                    shutil.copy2(source_filepath, dest_filepath) # メタデータ（更新日時など）もコピー
                    copied_count += 1
    print("-" * 30)
    print(f"コピー完了。コピーされたファイル数: {copied_count}, スキップされたファイル数: {skipped_count}")

# --- 使用例 ---
if __name__ == "__main__":
    # テスト用のディレクトリとファイルを作成
    # 既存のファイルと衝突しないように、ランダムな名前を使用することを推奨
    # 実行前に、以下のディレクトリとファイルを実際に作成してください

    # 例1: 特定のファイルのみをコピー
    print("--- 例1: 特定のファイルのみをコピー ---")
    source_folder_1 = "source_dir_1"
    dest_folder_1 = "dest_dir_1"
    files_to_copy_1 = ["file1.txt", "document.pdf"] # コピーしたいファイル名リスト

    # テスト用のファイル構造を作成 (実際には手動で作成するか、テストコードで作成)
    os.makedirs(os.path.join(source_folder_1, "sub_dir_A"), exist_ok=True)
    os.makedirs(os.path.join(source_folder_1, "sub_dir_B"), exist_ok=True)
    with open(os.path.join(source_folder_1, "file1.txt"), "w") as f: f.write("これはファイル1です。")
    with open(os.path.join(source_folder_1, "file2.log"), "w") as f: f.write("これはログファイルです。")
    with open(os.path.join(source_folder_1, "sub_dir_A", "document.pdf"), "w") as f: f.write("これはPDFドキュメントです。")
    with open(os.path.join(source_folder_1, "sub_dir_B", "report.txt"), "w") as f: f.write("これはレポートです。")

    recursive_copy_selected_files(source_folder_1, dest_folder_1, files_to_copy_1)
    print("\n")

    # 例2: 特定の拡張子のファイルをコピー (ワイルドカード使用)
    print("--- 例2: 特定の拡張子のファイルをコピー ---")
    source_folder_2 = "source_dir_2"
    dest_folder_2 = "dest_dir_2"
    files_to_copy_2 = ["*.txt", "*.log"] # .txt と .log 拡張子のファイルをコピー

    os.makedirs(os.path.join(source_folder_2, "data"), exist_ok=True)
    os.makedirs(os.path.join(source_folder_2, "logs"), exist_ok=True)
    with open(os.path.join(source_folder_2, "main.py"), "w") as f: f.write("Pythonスクリプト。")
    with open(os.path.join(source_folder_2, "data", "config.txt"), "w") as f: f.write("設定ファイル。")
    with open(os.path.join(source_folder_2, "logs", "app.log"), "w") as f: f.write("アプリケーションログ。")
    with open(os.path.join(source_folder_2, "image.png"), "w") as f: f.write("画像ファイル。")

    recursive_copy_selected_files(source_folder_2, dest_folder_2, files_to_copy_2)
    print("\n")

    # テスト用ディレクトリのクリーンアップ (オプション)
    # shutil.rmtree(source_folder_1)
    # shutil.rmtree(dest_folder_1)
    # shutil.rmtree(source_folder_2)
    # shutil.rmtree(dest_folder_2)
