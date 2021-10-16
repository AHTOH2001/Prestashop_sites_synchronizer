import os
from prestapyt import PrestaShopWebServiceError, PrestaShopWebService
import json
import time
from config import product_limit, friendly_sites, cached_images_path, images_logger as logger, prestashop_token


def get_images():
    logger.info('*****Start images synchronization...*****\n')
    total_images = 0
    total_products = 0
    total_start = time.time()

    if not os.path.isfile(cached_images_path):
        with open(cached_images_path, 'w') as fp:
            fp.write('{}')

    with open(cached_images_path, 'r') as fp:
        cached_images = json.load(fp)

    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))

        prestashop = PrestaShopWebService('http://{}/api'.format(site), prestashop_token, debug=True)

        start = time.time()
        logger.info('Start ids getting...')
        ref_to_id = dict()
        try:
            products = prestashop.get('products', options={'limit': product_limit, 'display': '[reference,id]'})[0]
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg)
            continue

        for product in products:
            ref_to_id[product.find('reference').text] = product.find('id').text

        logger.info('Get products ids in {}s...'.format(time.time() - start))

        start = time.time()
        logger.info('Start images getting...')
        new_images = 0
        new_products = 0
        for reference in ref_to_id:
            if reference in cached_images:
                continue

            try:
                images = prestashop.get('images/products/{}'.format(ref_to_id[reference]))[0]
            except PrestaShopWebServiceError:
                continue

            new_products += 1
            images_urls = []
            for image in images:
                new_images += 1
                images_urls.append(image.get('{http://www.w3.org/1999/xlink}href'))

            if len(images_urls) != 0:
                cached_images[reference] = images_urls

        total_images += new_images
        total_products += new_products
        logger.info(
            'Get {} new images for {} products in {}s...\n'.format(new_images, new_products, time.time() - start))

    with open(cached_images_path, 'w') as fp:
        json.dump(cached_images, fp)

    logger.info('Total get {} new images for {} products in {}s...\n'.format(
        total_images, total_products, time.time() - total_start))


def add_images():
    total_images = 0
    total_products = 0
    total_start = time.time()

    if not os.path.isfile(cached_images_path):
        with open(cached_images_path, 'w') as fp:
            fp.write('{}')

    with open(cached_images_path, 'r') as fp:
        cached_images = json.load(fp)

    logger.info('Start images adding...\n')
    for site in friendly_sites:
        logger.info('Start on site {}...'.format(site))

        prestashop = PrestaShopWebService('http://{}/api'.format(site), prestashop_token, debug=True)

        start = time.time()
        logger.info('Start references getting...')
        id_to_ref = dict()
        # active only products
        try:
            products = prestashop.get(
                'products', options={'limit': product_limit, 'display': '[reference,id]', 'filter[active]': '[1]'})[0]
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg)
            continue

        for product in products:
            id_to_ref[product.find('id').text] = product.find('reference').text

        logger.info('Get products references in {}s...'.format(time.time() - start))

        start = time.time()
        logger.info('Start images adding...')
        new_images = 0
        new_products = 0
        for id in id_to_ref:
            try:
                prestashop.get('images/products/{}'.format(id))[0]
            except PrestaShopWebServiceError:
                new_products += 1
                if id_to_ref[id] in cached_images:
                    for image_url in cached_images[id_to_ref[id]]:
                        try:
                            image = prestashop._execute(image_url, 'GET').content
                        except AttributeError:
                            logger.warning('Cache image expired, delete image from the cache')
                            del cached_images[id_to_ref[id]]
                        else:
                            new_images += 1
                            logger.debug('Added image {} for product {}'.format(image_url, id_to_ref[id]))
                            prestashop.add('/images/products/{}'.format(id),
                                           files=[('image', 'automatically_added_image.jpg', image)])

        total_images += new_images
        total_products += new_products
        logger.info('Add {} new images for {} products in {}s...\n'.format(
            new_images, new_products, time.time() - start))

    with open(cached_images_path, 'w') as fp:
        json.dump(cached_images, fp)

    logger.info(
        'Total add {} new images for {} products in {}s...\n'.format(total_images, total_products,
                                                                     time.time() - total_start))

    logger.info('*****End images synchronization!*****\n')
