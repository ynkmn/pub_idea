import optuna

# DBファイルのパス（例: study.db）
storage_url = "sqlite:///study.db"

# 既存のスタディ名を指定して読み込み
study = optuna.load_study(
    study_name="my_study",  # 作成時に使ったスタディ名
    storage=storage_url
)

# スタディの情報を確認
print("Best trial:")
print(study.best_trial)