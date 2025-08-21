import csv

with open('example.csv', mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)


import csv

data = [['商品名', '価格'], ['ペン', 100], ['ノート', 300], ['消しゴム', 50]]

with open('output.csv', mode='w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    for row in 
        writer.writerow(row)
