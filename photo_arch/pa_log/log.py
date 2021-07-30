# -*- coding: utf-8 -*-
import logging.handlers
import os
import time


def create_logger(file_log_level='DEBUG', file_name=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        if file_name is None:
            log_abs_path = os.path.abspath('./log')
            if not os.path.exists(log_abs_path):
                try:
                    os.makedirs(log_abs_path)
                except Exception as e:
                    _ = e
            file_name = os.path.join(log_abs_path, '%s.log' % time.strftime('%Y%m%d_%H%M%S'))

        formatter = logging.Formatter('[%(levelname)s] [%(asctime)s] '
                                      '[%(processName)s %(threadName)s] '
                                      '%(message)s')
        formatter.datefmt = '%Y-%m-%d %H:%M:%S'

        file_handler = logging.handlers.RotatingFileHandler(file_name, maxBytes=1024*1024*2, backupCount=256)
        file_handler.setLevel(getattr(logging, file_log_level))
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
    return logger


if __name__ == '__main__':
    test_logger = create_logger('INFO')
    test_logger.debug('this is debug')
    test_logger.info('this is info')
    test_logger.warning('this is warning')
    test_logger.error('this is error')
