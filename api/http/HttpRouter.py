from flask import request

from service.download_service import download


class Router:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.route('/download/', methods=['GET'])
        def download_file():
            return download(request)
