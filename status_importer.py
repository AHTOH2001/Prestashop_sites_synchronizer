from prestapyt import PrestaShopWebServiceError, PrestaShopWebServiceDict
import time
from config import product_limit, statuses_logger as logger, prestashop_token, main_site_for_statuses as main_site, dependent_sites_for_statuses as dependent_sites
import concurrent.futures


def get_disabled(site):
    start = time.time()
    prestashop = PrestaShopWebServiceDict('http://{}/api'.format(site), prestashop_token)

    logger.info('Start getting statuses from {}...'.format(site))

    try:
        products = prestashop.get(
            'products', options={'limit': product_limit, 'display': '[reference]', 'filter[active]': '[0]'})[
            'products']['product']
    except PrestaShopWebServiceError as e:
        logger.error(e.msg + '\n')
        return

    disabled_products = {prod['reference'] for prod in products}
    logger.info('Got {} disabled products from {} in {}s...\n'.format(
        len(disabled_products), main_site, round(time.time() - start, 2)))

    return disabled_products


def task_disabling_product(product, prestashop):
    logger.debug('Disabling product {} with id {}'.format(product['reference'], product['id']))
    full_product = prestashop.get('products', product['id'])
    full_product['product']['active'] = '0'
    # Pop these fields because they are not presented in the scheme, therefore edit will fail
    full_product['product'].pop('manufacturer_name')
    full_product['product'].pop('quantity')
    prestashop.edit('products', full_product)


def sync_statuses():
    logger.info('*****Start statuses synchronization...*****\n')
    total_start = time.time()

    disabled_products = get_disabled(main_site)

    total_disabled = 0
    for site in dependent_sites:
        logger.info('Start on site {}...'.format(site))
        start = time.time()

        prestashop = PrestaShopWebServiceDict('http://{}/api'.format(site), prestashop_token)

        try:
            products = prestashop.get(
                'products', options={'limit': product_limit, 'display': '[reference,id]', 'filter[active]': '[1]'})[
                'products']['product']
        except PrestaShopWebServiceError as e:
            logger.warning(e.msg + '\n')
            continue

        logger.info('Start of disabling statuses...')
        disabled_counter = 0

        with concurrent.futures.ThreadPoolExecutor() as pool:
            for product in products:
                cur_ref = product['reference']
                if cur_ref in disabled_products:
                    pool.submit(task_disabling_product, product, prestashop)
                    disabled_counter += 1

        total_disabled += disabled_counter        
        logger.info('Disabled {} statuses in {}s...\n'.format(disabled_counter, round(time.time() - start, 2)))        

    logger.info('Total disabled {} products in {}s...\n'.format(total_disabled, round(time.time() - total_start, 2)))
