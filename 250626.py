import logging

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# 標準出力用ハンドラ
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# ファイル出力用ハンドラ
file_handler = logging.FileHandler('output.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

logger.debug('debug message')
logger.info('info message')
