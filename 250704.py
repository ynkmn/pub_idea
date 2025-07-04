lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
chunk_size = 4
result = [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]
print(result)
# 出力: [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]
