import argparse
import threading
import time

import requests
from werkzeug.exceptions import abort
from flask import Flask, jsonify, request, send_file

from utils import config_parser


class Server:
    def __init__(self, host, port, default_media_path):
        self.host = host
        self.port = port
        self.media_paths = {i: default_media_path for i in range(1, 7)}

        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.get_home)
        self.app.add_url_rule('/home', view_func=self.get_home)
        self.app.add_url_rule('/screen/<number>', view_func=self.get_media_path)
        self.app.add_url_rule('/screen/<number>', view_func=self.update_media_path, methods=['PUT'])
        self.app.add_url_rule('/shutdown', view_func=self.shutdown)

        self.app.register_error_handler(404, self.page_not_found)

    def run_server(self):
        self.server = threading.Thread(target=self.app.run, kwargs={'host': self.host, 'port': self.port})
        self.server.start()
        return self.server

    def shutdown_server(self):
        request.get(f'http://{self.host}:{self.port}/shutdown')

    def get_home(self):
        return 'Hello api'

    def shutdown(self):
        terminate_func = request.environ.get('werkzeug.server.shutdown')
        if terminate_func:
            terminate_func()

    def page_not_found(self, error_description):
        return jsonify(error=str(error_description)), 404

    def get_media_path(self, number):
        number = int(number)
        if type(number) == int and 1 <= number <= 6:
            try:
                return send_file(self.media_paths[number],
                                 attachment_filename='python.jpg')
            except Exception as e:
                return str(e)
        else:
            abort(404, description='Screen number is int between 1 and 6.')

    def update_media_path(self, number):
        number = int(number)
        if type(number) == int and 1 <= number <= 6:
            request_body = dict(request.json)
            new_path = request_body.get('path', None)
            self.media_paths[number] = new_path
            return f'Successfully updated media path for screen {number}', 200
        else:
            abort(404, description='Screen number is int between 1 and 6.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')

    args = parser.parse_args()

    config = config_parser(args.config)
    server_host = config['HOST']
    server_port = int(config['PORT'])
    default_media_path = config['DEFAULT_MEDIA_PATH']
    server = Server(
        host=server_host,
        port=server_port,
        default_media_path=default_media_path
    )
    server.run_server()

    # Section for debug
    time.sleep(5)
    protocol = "http"
    route = 'screen/1'
    response = requests.put(f"{protocol}://{server_host}:{server_port}/{route}",
                            json={
                                "path": "/home/al/.local/src/repos/vk-backend/kostya.jpeg"
                            })
    print(response.text)
