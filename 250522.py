import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.debug('デバッグ情報')
logging.info('情報メッセージ')
logging.warning('警告メッセージ')
logging.error('エラーメッセージ')
logging.critical('致命的なエラーメッセージ')
