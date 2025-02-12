from typing import Any, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int
    msg: Optional[str] = None
    data: Optional[Any] = None

    @staticmethod
    def success(data):
        return ApiResponse(code=0, msg="success", data=data)

    @staticmethod
    def fail(msg, data):
        return ApiResponse(code=-1, msg=msg, data=data)
