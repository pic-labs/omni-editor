import logging
import os
import re
from urllib.parse import urlparse, unquote

import requests

logger = logging.getLogger(__name__)


def get_filename_from_url(url):
    # parse url
    parsed_url = urlparse(url)
    # extract path
    path = parsed_url.path
    # Retrieve the file name from the path and perform URL decoding."
    filename = unquote(os.path.basename(path))
    return filename


def get_filename_from_cd(cd):
    """
    Extract the filename from the Content-Disposition header.
    """
    if not cd:
        return None
    file_name = re.findall('filename="(.+)"', cd)
    if len(file_name) == 0:
        file_name = re.findall("filename=(.+)", cd)
    if len(file_name) == 0:
        return None
    return file_name[0]


def get_filename(url, response):
    if not response:
        return get_filename_from_url(url)
    cd = response.headers.get('content-disposition')
    return get_filename_from_cd(cd) or get_filename_from_url(url)


def download(url, sub_path, path="./tmp/data/omni-editor/download/{sub_path}/"):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            path = path.format(sub_path=sub_path)
            os.makedirs(path, exist_ok=True)
            file_name = get_filename(url, response)
            filepath = os.path.join(path, file_name)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            logger.info("file download success, url: %s, sub_path: %s", url, sub_path)
            return filepath
        else:
            raise ValueError(f"file download failed  code != 200, url: {url}, sub_path: {sub_path}")
    except Exception as e:
        logger.error("file download failed, url: %s, sub_path: %s", url, sub_path, exc_info=True)
        raise e
