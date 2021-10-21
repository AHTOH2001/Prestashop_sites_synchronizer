import sys

from logging import FileHandler
import logging
import os


def get_logger(name=__file__, file='log.txt', encoding='utf-8'):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s')

    # In the file
    fh = FileHandler(file, encoding=encoding)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # In stdout
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    return log


# Order has value
friendly_sites = os.environ.get('FRIENDLY_SITES').split()
main_site_for_statuses = os.environ.get('MAIN_SITE_FOR_STATUSES')
dependent_sites_for_statuses = os.environ.get('DEPENDENT_SITES_FOR_STATUSES').split()


product_limit = 99999
cached_images_path = 'caches/cached_images.json'
cached_descs_path = 'caches/cached_descs.json'
images_logger = get_logger(name='images logger', file='logs/images_log.txt')
descs_logger = get_logger(name='descs logger', file='logs/descs_log.txt')
statuses_logger = get_logger(name='statuses logger', file='logs/statuses_log.txt')
prestashop_token = os.environ.get('PRESTA_TOKEN')
