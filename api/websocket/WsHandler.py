import json
import logging

from api.ApiResponse import ApiResponse
from service.compile_video_service import CompileVideoService, CompileVideoParam
from service.img_service import ImgService, ImgResizeParam

logger = logging.getLogger(__name__)


async def handle(websocket):
    async for message in websocket:
        logger.info("handle ws begin, message:%s", message)
        try:
            data = json.loads(message)
        except Exception as e:
            logger.error("handle ws error, parse param fail, message:%s, error:%s", message, e, exc_info=True)
            await websocket.send(ApiResponse.fail(str(e), None).json())
            return

        try:
            result = {}
            if data["type"] == "compile_video":
                result = CompileVideoService.compile_video(data["task_id"],
                                                           CompileVideoParam.model_validate(data.get("param")))
            elif data["type"] == "img_resize":
                result = ImgService.resize_img(data["task_id"], ImgResizeParam.model_validate(data.get("param")))

            result["task_id"] = data["task_id"]
            await websocket.send(ApiResponse.success(result).json())
            logger.info("handle ws end, result:%s", json.dumps(result))
        except Exception as e:
            logger.error("handle ws error, task_id:%s, error:%s", data["task_id"], e, exc_info=True)
            await websocket.send(ApiResponse.fail(str(e), {"task_id": data["task_id"]}).json())
