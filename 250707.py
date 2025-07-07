python3 myscript.py
if [ $? -ne 0 ]; then
  echo "python3でエラーが発生しました"
  # 必要に応じて処理を中断
  exit 1
fi
