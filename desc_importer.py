from prestapyt import PrestaShopWebServiceError, PrestaShopWebServiceDict
import json
import time
from config import product_limit, friendly_sites, cached_descs_path, descs_logger as logger, prestashop_token


def get_desc():
    logger.info('*****Start descriptions synchronization...*****\n')
    total_descs = 0
    total_start = time.time()
    with open(cached_descs_path, 'r', encoding='UTF-8') as fp:
        cached_descs = json.load(fp)

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))

        prestashop = PrestaShopWebServiceDict('http://{}/api'.format(site), prestashop_token)
        start = time.time()
        logger.info('Start descriptions getting...')
        try:
            products = prestashop.get(
                'products', options={'limit': product_limit, 'display': '[reference,description,description_short]'})[
                'products']['product']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg)
            continue

        new_descs = 0

        for product in products:
            cur_ref = product['reference']
            for lang in product['description']['language']:
                if lang['value'] != '':
                    if (cur_ref not in cached_descs):
                        cached_descs[cur_ref] = {'desc': {}, 'desc_s': {}}

                    if lang['attrs']['id'] not in cached_descs[cur_ref]['desc']:
                        new_descs += 1
                        cached_descs[cur_ref]['desc'][lang['attrs']['id']] = lang['value']

            for lang in product['description_short']['language']:
                if lang['value'] != '':
                    if (cur_ref not in cached_descs):
                        cached_descs[cur_ref] = {'desc': {}, 'desc_s': {}}

                    if lang['attrs']['id'] not in cached_descs[cur_ref]['desc_s']:
                        new_descs += 1
                        cached_descs[cur_ref]['desc_s'][lang['attrs']['id']] = lang['value']

        total_descs += new_descs
        logger.info('Get {} new descriptions in {}s...\n'.format(new_descs, round(time.time() - start, 2)))

    with open(cached_descs_path, 'w', encoding='UTF-8') as fp:
        json.dump(cached_descs, fp)

    logger.info('Total get {} new descriptions in {}s...\n'.format(total_descs, round(time.time() - total_start, 2)))


def add_desc():
    total_descs = 0
    total_start = time.time()
    with open(cached_descs_path, 'r', encoding='UTF-8') as fp:
        cached_descs = json.load(fp)

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))

        prestashop = PrestaShopWebServiceDict('http://{}/api'.format(site), prestashop_token)
        start = time.time()
        logger.info('Start descriptions adding...')
        try:
            products = prestashop.get(
                'products', options={'limit': product_limit,
                                     'display': '[reference,id,description,description_short]'})['products']['product']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg)
            continue

        new_descs_counter = 0

        # address_data = prestashop.get('addresses', 934)
        # address_scheme = prestashop.get('addresses', options={'schema': 'blank'})
        # address_data['address']['firstname'] = 'Robert'
        # prestashop.edit('addresses', address_data)
        # prod_data = prestashop.get('products', 22510)
        # prod_scheme = prestashop.get('products', options={'schema': 'blank'})
        # diff = set(prod_data['product'].keys()) - set(prod_scheme['product'].keys())
        # prestashop.add('products', prod_scheme)
        # exit()

        for product in products:
            cur_ref = product['reference']
            if (cur_ref not in cached_descs):
                continue

            # for lang in product['description']['language']:
                # if lang['value'] == '' and lang['attrs']['id'] in cached_descs[cur_ref]['desc']:
            new_descs = cached_descs[cur_ref]['desc']
            # if new_desc[lang['attrs']['id']]:

            # full_product['product']['description']['language'] = list(map(
            #     lambda cur_lang: {'attrs': {'id': cur_lang['attrs']['id']}, 'value': new_descs[cur_lang['attrs']['id']]} if cur_lang['attrs']['id'] in new_descs else cur_lang,
            #     full_product['product']['description']['language']))
            res_languages = []
            for lang in product['description']['language']:
                cur_id = lang['attrs']['id']
                cur_value = lang['value']
                if cur_id in new_descs and cur_value == '':
                    res_languages.append({'attrs': {'id': cur_id}, 'value': new_descs[cur_id]})
                else:
                    res_languages.append(lang)

            if product['description']['language'] != res_languages:
                full_product = prestashop.get('products', product['id'])
                full_product['product']['description']['language'] = res_languages
                new_descs_counter += 1
                logger.debug('Adding descriptions for product {}'.format(cur_ref))
                # Pop these fields because they are not presented in the scheme and edit will fail
                full_product['product'].pop('manufacturer_name')
                full_product['product'].pop('quantity')
                prestashop.edit('products', full_product)
                # prestashop.add('products', cached_descs[cur_ref]['desc'][lang['attrs']['id']])
                exit()

            for lang in product['description_short']['language']:
                if lang['value'] == '':
                    if lang['attrs']['id'] in cached_descs[cur_ref]['desc_s']:
                        new_descs_counter += 1
                        logger.debug('Adding short description with lang {} for product {}'.format(
                            lang['attrs']['id'], cur_ref))
                        cached_descs[cur_ref]['desc_s'][lang['attrs']['id']]

        total_descs += new_descs_counter
        logger.info('Get {} new descriptions in {}s...\n'.format(new_descs_counter, round(time.time() - start, 2)))

    with open(cached_descs_path, 'w', encoding='UTF-8') as fp:
        json.dump(cached_descs, fp)

    logger.info('Total add {} new description in {}s...\n'.format(total_descs, time.time() - total_start))

    logger.info('*****End descriptions synchronization!*****\n')
