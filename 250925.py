import csv

def convert_temperature_to_kelvin(celsius: float) -> float:
    """摂氏→ケルビン変換"""
    return celsius + 273.15

def process_csv(input_file: str, output_file: str):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # [Name] セクション
        if line.strip() == "[Name]":
            output_lines.append(line)
            i += 1
            name = lines[i].strip()
            output_lines.append(name)
            i += 1

            # [Data] セクション
            if lines[i].strip() == "[Data]":
                output_lines.append(lines[i])  # [Data]
                i += 1

                # ヘッダー
                header = lines[i].split(",")
                output_lines.append(lines[i])
                i += 1

                # transient-temperature の場合、temperature列を変換
                if name == "transient-temperature":
                    if "temperature" in header:
                        temp_idx = header.index("temperature")
                        while i < len(lines) and lines[i] and not lines[i].startswith("[Name]"):
                            row = lines[i].split(",")
                            if row[temp_idx]:
                                celsius = float(row[temp_idx])
                                row[temp_idx] = f"{convert_temperature_to_kelvin(celsius):.2f}"
                            output_lines.append(",".join(row))
                            i += 1
                    else:
                        # temperature列がない場合はそのまま
                        while i < len(lines) and lines[i] and not lines[i].startswith("[Name]"):
                            output_lines.append(lines[i])
                            i += 1
                else:
                    # 他のNameは変換せずそのまま
                    while i < len(lines) and lines[i] and not lines[i].startswith("[Name]"):
                        output_lines.append(lines[i])
                        i += 1
            else:
                i += 1
        else:
            i += 1

    # 出力
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        for line in output_lines:
            f.write(line + "\n")


# 実行例
if __name__ == "__main__":
    process_csv("input.csv", "output.csv")