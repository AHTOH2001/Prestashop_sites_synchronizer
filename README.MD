# Script for synchronization images, statuses and descriptions in different prestashop sites by product reference

cache format:

- cached_images.json:
    - {reference: [img_url_1, img_url_2, ...]}
    
- cached_descs.json:
    - {reference: {'desc': {lang_iso_1: value, lang_iso_2: value, ...}, 'desc_s': {lang_iso_1: value,  ...}}, ...}
