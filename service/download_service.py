import logging
import os

from flask import send_from_directory, abort

from config.common_config import FILE_DIR

logger = logging.getLogger(__name__)


def download(request):
    file_name = request.args.get('file_name')
    if not os.path.exists(os.path.join(FILE_DIR, file_name)):
        logger.info("file not found, file_name:%s", file_name)
        return abort(404, description="file not found")
    try:
        return send_from_directory(FILE_DIR, file_name, as_attachment=True)
    except Exception as e:
        logger.error("download error, file_name:%s, error:%s", file_name, e, exc_info=True)
        return abort(500, description="download error")
