from flask import request, send_from_directory

from service.download_service import download


class Router:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        @self.app.route('/download/', methods=['GET'])
        def download_file():
            return download(request)

        @self.app.route('/index.html')
        def serve_index():
            return send_from_directory('static', 'index.html')

        @self.app.route('/audio/<path:filename>')
        def get_image(filename):
            return send_from_directory('static/audio', filename)
