from concurrent.futures.thread import ThreadPoolExecutor
import os
from prestapyt import PrestaShopWebServiceError, PrestaShopWebServiceDict
import json
import time
from config import product_limit, friendly_sites, cached_descs_path, descs_logger as logger, prestashop_token
import re


def get_descs():
    logger.info('*****Start descriptions synchronization...*****\n')
    total_descs = 0
    total_start = time.time()
    pattern_for_removing_empty_tags = r'<([^>\s]+)[^>]*>(?:\s*(?:<br \/>|&nbsp;|&thinsp;|&ensp;|&emsp;|&#8201;|&#8194;|&#8195;)\s*)*<\/\1>'
    cached_descs = {}

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))
        start = time.time()

        prestashop = PrestaShopWebServiceDict('http://{}/api'.format(site), prestashop_token)

        try:
            products = prestashop.get(
                'products', options={'limit': product_limit, 'display': '[reference,description,description_short]'})[
                'products']['product']
            languages = prestashop.get(
                'languages', options={'limit': product_limit, 'display': '[id,iso_code]'})['languages']['language']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg + '\n')
            continue

        logger.info('Start descriptions getting...')
        iso_codes = {lang['id']: lang['iso_code'] for lang in languages}
        new_descs = 0

        for product in products:
            cur_ref = product['reference']
            for lang in product['description']['language']:
                iso_code = iso_codes[lang['attrs']['id']]
                value = re.sub(pattern_for_removing_empty_tags, '', lang['value']).strip()
                if value != '':
                    if (cur_ref not in cached_descs):
                        cached_descs[cur_ref] = {'desc': {}, 'desc_s': {}}

                    if iso_code not in cached_descs[cur_ref]['desc']:
                        new_descs += 1
                        cached_descs[cur_ref]['desc'][iso_code] = value

            for lang in product['description_short']['language']:
                iso_code = iso_codes[lang['attrs']['id']]
                value = re.sub(pattern_for_removing_empty_tags, '', lang['value']).strip()
                if value != '':
                    if (cur_ref not in cached_descs):
                        cached_descs[cur_ref] = {'desc': {}, 'desc_s': {}}

                    if iso_code not in cached_descs[cur_ref]['desc_s']:
                        new_descs += 1
                        cached_descs[cur_ref]['desc_s'][iso_code] = value

        total_descs += new_descs
        logger.info('Got {} new descriptions in {}s...\n'.format(new_descs, round(time.time() - start, 2)))

    with open(cached_descs_path, 'w', encoding='UTF-8') as fp:
        json.dump(cached_descs, fp)

    logger.info('Total got {} new descriptions in {}s...\n'.format(total_descs, round(time.time() - total_start, 2)))


def task_adding_descriptions(product, prestashop, desc_languages, short_desc_languages):
    full_product = prestashop.get('products', product['id'])
    full_product['product']['description']['language'] = desc_languages
    full_product['product']['description_short']['language'] = short_desc_languages
    logger.debug('Adding new descriptions for product {}'.format(product['reference']))
    # Pop these fields because they are not presented in the scheme, therefore edit will fail
    full_product['product'].pop('manufacturer_name')
    full_product['product'].pop('quantity')
    prestashop.edit('products', full_product)


def add_descs():
    total_descs = 0
    total_start = time.time()

    if not os.path.isfile(cached_descs_path):
        with open(cached_descs_path, 'w', encoding='UTF-8') as fp:
            fp.write('{}')

    with open(cached_descs_path, 'r', encoding='UTF-8') as fp:
        cached_descs = json.load(fp)

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))
        start = time.time()

        prestashop = PrestaShopWebServiceDict('http://{}/api'.format(site), prestashop_token)

        try:
            products = prestashop.get(
                'products', options={'limit': product_limit,
                                     'display': '[reference,id,description,description_short]'})['products']['product']
            languages = prestashop.get(
                'languages', options={'limit': product_limit, 'display': '[id,iso_code]'})['languages']['language']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg + '\n')
            continue

        logger.info('Start descriptions adding...')
        iso_codes = {lang['id']: lang['iso_code'] for lang in languages}
        new_descs_counter = 0
        with ThreadPoolExecutor() as pool:
            for product in products:
                cur_ref = product['reference']
                if (cur_ref not in cached_descs):
                    continue

                # DESCRIPTIONS
                new_descs = cached_descs[cur_ref]['desc']
                # Trying to update as much languages as possible
                desc_languages = []
                for lang in product['description']['language']:
                    cur_id = lang['attrs']['id']
                    cur_value = lang['value']
                    if iso_codes[cur_id] in new_descs and cur_value == '':
                        desc_languages.append({'attrs': {'id': cur_id}, 'value': new_descs[iso_codes[cur_id]]})
                    else:
                        desc_languages.append(lang)

                # SHORT DESCRIPTIONS
                new_descs_s = cached_descs[cur_ref]['desc_s']
                # Trying to update as much languages as possible
                short_desc_languages = []
                for lang in product['description_short']['language']:
                    cur_id = lang['attrs']['id']
                    cur_value = lang['value']
                    if iso_codes[cur_id] in new_descs_s and cur_value == '':
                        short_desc_languages.append({'attrs': {'id': cur_id}, 'value': new_descs_s[iso_codes[cur_id]]})
                    else:
                        short_desc_languages.append(lang)

                # COMMITING CHANGES
                if product['description']['language'] != desc_languages or product['description_short']['language'] != short_desc_languages:  # Something changed
                    pool.submit(task_adding_descriptions, product, prestashop, desc_languages, short_desc_languages)
                    new_descs_counter += 1

        total_descs += new_descs_counter
        logger.info('Added {} new descriptions in {}s...\n'.format(new_descs_counter, round(time.time() - start, 2)))

    logger.info('Total added {} new description in {}s...\n'.format(total_descs, time.time() - total_start))

    logger.info('*****End descriptions synchronization!*****\n')
