from images_importer import get_images, add_images
from desc_importer import get_descs, add_descs
from names_importer import add_names, get_names
from status_importer import sync_statuses
from config import root_logger as logger

if __name__ == '__main__':
    try:
        sync_statuses()
        get_images()
        add_images()
        get_names()
        add_names()
        get_descs()
        add_descs()
    except Exception as exc:
        logger.exception('main exc')
