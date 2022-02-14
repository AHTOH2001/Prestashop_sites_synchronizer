from prestapyt import PrestaShopWebServiceError, PrestaShopWebServiceDict
import time
from config import product_limit, names_logger as logger, prestashop_token, friendly_sites, cached_names_path
import os
from concurrent.futures.thread import ThreadPoolExecutor
import json


def get_names():
    logger.info('*****Start names synchronization...*****\n')
    total_names = 0
    total_start = time.time()
    cached_names = {}

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))
        start = time.time()

        prestashop = PrestaShopWebServiceDict('{}/api'.format(site), prestashop_token)

        try:
            products = prestashop.get(
                'products', options={'limit': product_limit, 'display': '[reference,name]'})['products']['product']
            languages = prestashop.get(
                'languages', options={'limit': product_limit, 'display': '[id,iso_code]'})['languages']['language']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg + '\n')
            continue

        logger.info('Start names getting...')
        iso_codes = {lang['id']: lang['iso_code'] for lang in languages}
        new_names = 0

        for product in products:
            cur_ref = product['reference']
            for lang in product['name']['language']:
                iso_code = iso_codes[lang['attrs']['id']]
                value = lang['value'].strip()
                if value != '':
                    if (cur_ref not in cached_names):
                        cached_names[cur_ref] = {}

                    if iso_code not in cached_names[cur_ref]:
                        new_names += 1
                        cached_names[cur_ref][iso_code] = value

        total_names += new_names
        logger.info('Got {} new names in {}s...\n'.format(new_names, round(time.time() - start, 2)))

    with open(cached_names_path, 'w', encoding='UTF-8') as fp:
        json.dump(cached_names, fp)

    logger.info('Total got {} new names in {}s...\n'.format(total_names, round(time.time() - total_start, 2)))


def task_adding_names(product, prestashop, name_languages):
    try:
        full_product = prestashop.get('products', product['id'])
    except Exception as exc:
        logger.error(f'{exc} for id = {product["id"]}')
        return
    full_product['product']['name']['language'] = name_languages
    logger.debug('Adding new names for product {}'.format(product['reference']))
    # Pop these fields because they are not presented in the scheme, therefore edit will fail
    full_product['product'].pop('manufacturer_name', None)
    full_product['product'].pop('quantity', None)
    full_product['product'].pop('position_in_category', None)
    try:
        prestashop.edit('products', full_product)
    except Exception as exc:
        logger.error(f'{exc} for id = {product["id"]}')
        return


def add_names():
    total_names = 0
    total_start = time.time()

    if not os.path.isfile(cached_names_path):
        with open(cached_names_path, 'w', encoding='UTF-8') as fp:
            fp.write('{}')

    with open(cached_names_path, 'r', encoding='UTF-8') as fp:
        cached_names = json.load(fp)

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))
        start = time.time()

        prestashop = PrestaShopWebServiceDict('{}/api'.format(site), prestashop_token)

        try:
            products = prestashop.get(
                'products', options={'limit': product_limit, 'display': '[reference,id,name]'})['products']['product']
            languages = prestashop.get(
                'languages', options={'limit': product_limit, 'display': '[id,iso_code]'})['languages']['language']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg + '\n')
            continue

        logger.info('Start names adding...')
        iso_codes = {lang['id']: lang['iso_code'] for lang in languages}
        new_names_counter = 0
        with ThreadPoolExecutor() as pool:
            for product in products:
                cur_ref = product['reference']
                if (cur_ref not in cached_names):
                    continue

                new_names = cached_names[cur_ref]
                name_languages = []
                for lang in product['name']['language']:
                    cur_id = lang['attrs']['id']
                    cur_value = lang['value']
                    if iso_codes[cur_id] in new_names and (cur_value == '' or site == 'http://nk7i.l.dedikuoti.lt'):
                        name_languages.append({'attrs': {'id': cur_id}, 'value': new_names[iso_codes[cur_id]]})
                    else:
                        name_languages.append(lang)

                if product['name']['language'] != name_languages:
                    pool.submit(task_adding_names, product, prestashop, name_languages)
                    new_names_counter += 1

        total_names += new_names_counter
        logger.info('Added {} new names in {}s...\n'.format(new_names_counter, round(time.time() - start, 2)))

    logger.info('Total added {} new names in {}s...\n'.format(total_names, time.time() - total_start))

    logger.info('*****End names synchronization!*****\n')
