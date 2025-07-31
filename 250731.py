def read_until_slash_line(filepath):
    lines = []

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() == '/':  # スラッシュのみの行（空白除く）
                break
            lines.append(line)

    return lines
