with open('file.txt', 'r', encoding='utf-8') as file:
    content = file.read()

new_content = content.replace('置換前の文字列', '置換後の文字列')

with open('file.txt', 'w', encoding='utf-8') as file:
    file.write(new_content)



lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
chunk_size = 4
result = [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]
print(result)
# 出力: [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]
