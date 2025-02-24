import asyncio
import logging
import os
import threading

import websockets
from flask import Flask
from flask_cors import CORS
from gevent.pywsgi import WSGIServer

from api.http.HttpRouter import Router
from api.websocket.WsHandler import handle
from config import log_config
from config.common_config import FILE_DIR

log_config.init()
os.makedirs(FILE_DIR, exist_ok=True)
app = Flask(__name__)
CORS(app, resources=r'/*', supports_credentials=True)
logger = logging.getLogger(__name__)

async def start_websocket_server():
    async with websockets.serve(handle, '0.0.0.0', 8765, ping_interval=60, ping_timeout=600):
        await asyncio.Future()


def run_websocket_server():
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(start_websocket_server())
    new_loop.run_forever()


if __name__ == '__main__':
    # start websocket server and http server
    websocket_thread = threading.Thread(target=run_websocket_server)
    websocket_thread.setDaemon(True)
    websocket_thread.start()

    routes = Router(app)
    http_server = WSGIServer(('0.0.0.0', 8080), app)
    http_server.serve_forever()
