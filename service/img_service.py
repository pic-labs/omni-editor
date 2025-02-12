import logging

from pydantic import BaseModel

from config.common_config import FILE_DIR
from utils.file_downloader import download
from utils.img_utils import img_resize

logger = logging.getLogger(__name__)


class ImgResizeParam(BaseModel):
    img: str
    width: int
    height: int


class ImgService:
    @staticmethod
    def resize_img(task_id: str, param: ImgResizeParam):
        material = download(param.img, task_id)
        img, format = img_resize(material, param.width, param.height)
        img_name = task_id + "." + format.lower()
        path = FILE_DIR + img_name
        img.save(path)
        logger.info("img_resize success, task_id: %s, img: %s", task_id, img_name)
        return {"img": img_name}
