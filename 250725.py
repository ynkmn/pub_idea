import argparse

parser = argparse.ArgumentParser(description="Example script with development mode argument")

# '--dev'オプションを追加（フラグ引数、つけるだけでTrueになる）
parser.add_argument('--dev', action='store_true', help='Run in development environment mode')

args = parser.parse_args()

if args.dev:
    print("開発環境モードで実行中")
else:
    print("通常モードで実行中")
