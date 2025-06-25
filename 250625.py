import csv

with open('filename.csv', 'r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row)  # rowは辞書型で、キーがヘッダー、値が各行のデータ
