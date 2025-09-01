



import optuna

# DBファイルのパス（例: study.db）
storage_url = "sqlite:///study.db"

# 既存のスタディ名を指定して読み込み
study = optuna.load_study(
    study_name="my_study",  # 作成時に使ったスタディ名
    storage=storage_url
)
summaries = optuna.study.get_all_study_summaries(storage=storage_url)
for s in summaries:
    print(s.study_name, s.best_value)


# スタディの情報を確認
print("Best trial:")
print(study.best_trial)


import matplotlib.pyplot as plt

df = study.trials_dataframe()

plt.plot(df["number"], df["value"], marker="o")
plt.xlabel("Trial")
plt.ylabel("Objective Value (Error)")
plt.title("Error History")
plt.show()


