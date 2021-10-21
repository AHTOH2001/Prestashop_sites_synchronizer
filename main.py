from images_importer import get_images, add_images
from desc_importer import get_descs, add_descs
from status_importer import sync_statuses

if __name__ == '__main__':
    sync_statuses()
    get_descs()
    add_descs()
    get_images()
    add_images()
