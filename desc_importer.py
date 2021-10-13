from prestapyt import PrestaShopWebServiceError, PrestaShopWebService, PrestaShopWebServiceDict
import json
import time
from config import product_limit, friendly_sites, cached_descs_path, descs_logger as logger, prestashop_token


def get_desc():
    logger.info('*****Start description synchronization...*****\n')
    total_descs = 0
    # total_products = 0
    total_start = time.time()
    with open(cached_descs_path, 'r', encoding='UTF-8') as fp:
        cached_descs = json.load(fp)
        cached_refs = set(cached_descs.keys())

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))

        prestashop = PrestaShopWebServiceDict(
            'http://{}/api'.format(site), prestashop_token)
        # start = time.time()
        # logger.info('Start ids getting...')
        # ref_to_id = dict()
        start = time.time()
        logger.info('Start descriptions getting...')
        try:
            products = prestashop.get('products', options={
                                      'limit': product_limit, 'display': '[reference,id,description]'})['products']['product']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg)
            continue

        # for product in products:
        #     ref_to_id[product['reference']] = product['id']

        # logger.info('Get products ids in {}s...'.format(time.time() - start))

        new_descs = 0
        # new_products = 0

        for product in products:
            if product['reference'] not in cached_refs and any(lang['value'] != '' for lang in product['description']['language']):
                new_descs += 1
                description = [lang['value']
                               for lang in product['description']['language']]
                cached_descs[product['reference']] = description
                cached_refs.add(product['reference'])

        total_descs += new_descs
        logger.info(
            'Get {} new descriptions in {}s...\n'.format(new_descs, round(time.time() - start, 2)))
       # for reference in ref_to_id:
       #     if reference in cached_descs:
       #         continue

       #     try:
       #         product = prestashop.get(
       #             'products/{}'.format(ref_to_id[reference]))['product']
       #     except PrestaShopWebServiceError:
       #         continue
       #     desc = product['description']
       #     # desc_s = product['description_short']
       #     # TODO figure out how store descriptions in one json file or in two different or smt else
       #     new_products += 1
       #     images_urls = []
       #     for image in images:
       #         new_descs += 1
       #         images_urls.append(
       #             image.get('{http://www.w3.org/1999/xlink}href'))

       #     if len(images_urls) != 0:
       #         cached_descs[reference] = images_urls

       # total_descs += new_descs
       # total_products += new_products
       # logger.info(
       #     'Get {} new images for {} products in {}s...\n'.format(new_descs, new_products, time.time() - start))

    with open(cached_descs_path, 'w', encoding='UTF-8') as fp:
        json.dump(cached_descs, fp)

    logger.info(
        'Total get {} new descriptions in {}s...\n'.format(total_descs, round(time.time() - total_start, 2)))


def add_desc():
    total_images = 0
    total_products = 0
    total_start = time.time()
    with open(cached_descs_path, 'r') as fp:
        cached_images = json.load(fp)

    logger.info('Start images adding...\n')
    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))

        prestashop = PrestaShopWebService(
            'http://{}/api'.format(site), prestashop_token)

        start = time.time()
        logger.info('Start references getting...')
        id_to_ref = dict()
        # active only products
        try:
            products = prestashop.get('products',
                                      options={'limit': product_limit, 'display': '[reference,id]',
                                               'filter[active]': '[1]'})[0]
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg)
            continue

        for product in products:
            id_to_ref[product.find('id').text] = product.find('reference').text

        logger.info('Get products references in {}s...'.format(
            time.time() - start))

        start = time.time()
        logger.info('Start images adding...')
        new_images = 0
        new_products = 0
        for id in id_to_ref:
            try:
                images = prestashop.get('images/products/{}'.format(id))[0]
            except PrestaShopWebServiceError:
                new_products += 1
                images_urls = []
                if id_to_ref[id] in cached_images:
                    for image_url in cached_images[id_to_ref[id]]:
                        try:
                            image = prestashop._execute(
                                image_url, 'GET').content
                        except AttributeError:
                            logger.warning(
                                'Cache image expired, delete image from cache')
                            del cached_images[id_to_ref[id]]
                        else:
                            new_images += 1
                            logger.debug('Added image {} for product {}'.format(
                                image_url, id_to_ref[id]))
                            prestashop.add('/images/products/{}'.format(id),
                                           files=[('image', 'automatically_added_image.jpg', image)])

        total_images += new_images
        total_products += new_products
        logger.info(
            'Add {} new images for {} products in {}s...\n'.format(new_images, new_products, time.time() - start))

    with open(cached_descs_path, 'w') as fp:
        json.dump(cached_images, fp)

    logger.info(
        'Total add {} new images for {} products in {}s...\n'.format(total_images, total_products,
                                                                     time.time() - total_start))

    logger.info('*****End description synchronization!*****\n')
