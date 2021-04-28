import argparse
import pathlib

from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import abort
from pydantic import ValidationError

from app.api.utils import config_parser, ScreenInfo, MediaInfo, Playlist, FinishedEvent

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, dest='config')

args = parser.parse_args()

config = config_parser(args.config)
server_host = config['HOST']
server_port = int(config['PORT'])
default_media_location = config['DEFAULT_MEDIA_LOCATION']
default_media_type = config['DEFAULT_MEDIA_TYPE']
default_media_duration = config['DEFAULT_MEDIA_DURATION']
screens_info = {i: {"location": default_media_location,
                    "duration": default_media_duration,
                    "media_type": default_media_type} for i in range(1, 7)}
screen_sids = {i: "" for i in range(1, 7)}
playlists = {i: [] for i in range(1, 7)}
playlist_iters = {i: iter([]) for i in range(1, 7)}


# playlist = [
#     {
#         "location": "/home/al/.local/src/repos/vk-backend/jesus.jpg",
#         "duration": 3,
#         "media_type": "img"
#     },
#     {
#         "location": "/home/al/.local/src/repos/vk-backend/kostya.jpeg",
#         "duration": 3,
#         "media_type": "img"
#     },
#     {
#         "location": "/home/al/.local/src/repos/vk-backend/jesus.jpg",
#         "duration": 3,
#         "duration": "img",
#     },
#     {
#         "location": "/home/al/.local/src/repos/vk-backend/dawg.webm",
#         "duration": 3,
#         "media_type": "vid"
#     }
# ]
# playlist_iter = iter(playlist)


@app.route("/")
def index():
    return '''
    screen_number -- целое число от 1 до 6<br/>
        endpoints:<br/>
            [GET] /screen/screen_number/file -- возвращает файл, который можно стримить в VLC<br/>
            [GET] /screen/screen_number -- возвращает json вида {"media_type" : "some_media_type",
                                                                "duration" : "some_duration",
                                                                "url" : "some_url"},
            где url - путь, по которому доступен файл для экрана screen_number <br/>
            [PUT] /screen/screen_number -- принимает json вида {"media_type": "", "location" : "", "duration" : ""} и
            обновляет данные для экрана, где some_media_type -- это vid, img или gif<br/>
            [PUT] /playlist/screen_number -- принимает json список с предметами {"media_type": "", "location" : "",
             "duration" : ""} <br/>
            [GET] /refresh -- обновить все экраны <br/>
            [GET] /refresh/screen_number -- обновить экран screen_number <br/>
            '''


@app.route("/screen/<int:screen_number>/file", methods=['GET'])
def get_media_file(screen_number: int):
    screen_number = verify_screen_number(screen_number)
    try:
        return send_file(screens_info[screen_number]['location'],
                         attachment_filename='python.jpg')
    except Exception as e:
        return str(e)


@app.route("/screen/<int:screen_number>", methods=['GET'])
def get_screen_info(screen_number: int):
    screen_number = verify_screen_number(screen_number)
    try:
        url = f"http://{server_host}:{server_port}/screen/{screen_number}/file"
        duration = screens_info[screen_number]['duration']
        media_type = screens_info[screen_number]['media_type']
        info = ScreenInfo(
            url=url,
            duration=duration,
            media_type=media_type
        )
        return info.json()
    except Exception as e:
        return str(e)


@app.route('/screens', methods=['GET'])
def get_screens():
    return jsonify(screens_info)


@app.route('/screen/<int:screen_number>', methods=['PUT'])
def update_media_info(screen_number, custom_body=None):
    screen_number = verify_screen_number(screen_number)
    if request.json:
        request_body = dict(request.json)
        media_info = ''
        try:
            media_info = MediaInfo(**request_body)
            print(media_info)
        except ValidationError as e:
            print(e)
            return e, 400
        if media_info.location:
            screens_info[screen_number]['location'] = media_info.location
        if media_info.duration:
            screens_info[screen_number]['duration'] = media_info.duration
        if media_info.media_type:
            screens_info[screen_number]['media_type'] = media_info.media_type
    if custom_body:
        media_info = MediaInfo(**custom_body)
        if media_info.location:
            screens_info[screen_number]['location'] = media_info.location
        if media_info.duration:
            screens_info[screen_number]['duration'] = media_info.duration
        if media_info.media_type:
            screens_info[screen_number]['media_type'] = media_info.media_type
    socketio.emit('screen refresh',
                  {'msg': f'Screen ${screen_number} should be refreshed', 'screen_number': screen_number})
    return f'Successfully updated media path for screen {screen_number}', 200


@app.route("/playlist/<int:screen_number>", methods=['PUT'])
def update_playlist(screen_number: int):
    playlist = []
    screen_number = verify_screen_number(screen_number)
    try:
        # print(request.json)
        request_body = dict(request.json)
        playlist = Playlist(__root__=request_body['items'])
    except ValidationError as e:
        return e, 400
    # print(playlist)
    playlists[screen_number].clear()
    # playlist_iters[screen_number].clear()
    playlists[screen_number] = playlist.__root__.copy()
    playlist_iters[screen_number] = iter(playlists[screen_number])
    return f'Successfully updated playlist for screen #{screen_number}', 200


@app.route("/playlist/<int:screen_number>", methods=['GET'])
def get_playlist(screen_number: int):
    screen_number = verify_screen_number(screen_number)
    pl = Playlist(__root__=playlists[screen_number])
    return pl.json()
@app.route('/refresh', methods=['GET'])
def refresh_screens():
    socketio.emit('screen refresh', {"msg": "All screens should be refreshed", "screen_number": 0})
    return 'Signal to update all screens was sent', 200


@app.route('/refresh/<int:screen_number>', methods=['GET'])
def refresh_screen(screen_number):
    screen_number = verify_screen_number(screen_number)
    socketio.emit('screen refresh',
                  {"msg": f"Screen{screen_number} should be refreshed", "screen_number": screen_number})
    return f"Signal to update {screen_number} screen was sent", 200


@app.route('/sids', methods=['GET'])
def get_sids():
    return jsonify(screen_sids)


@app.errorhandler(404)
def page_not_found(error_description):
    return jsonify(error=str(error_description)), 404


@socketio.on('message')
def on_message(data):
    print("I received a message!")
    print(data)


@socketio.on('my message')
def on_my_message(data):
    print('I received a message!')
    print(data)


@socketio.on('connect')
def test_connect(sid=111):
    sid = request.sid
    emit('my message', {'data': 'Connected'})
    print('Client connected:', sid)


@socketio.on('disconnect')
def test_disconnect(sid=111):
    print('Client disconnected:', sid)


@socketio.on('screen refresh')
def on_media_updated(data):
    print(data)
    screen = data['screen']
    new_path = data['path']
    new_type = data['type']
    if screen:
        screen = int(screen)
    if new_path:
        screens_info[screen]['path'] = new_path
    if new_type:
        screens_info[screen]['type'] = new_type
    return 'ok', 200


@socketio.on('screen number')
def on_screen_number(data):
    screen_sids[data['screen']] = data['sid']


@socketio.on('finished playing')
def on_finish_playing(data):
    finished_event = FinishedEvent.parse_raw(data)
    screen_number = finished_event.screen_number
    print(playlist_iters.keys())
    print(playlist_iters.values())
    try:
        item = next(playlist_iters[screen_number])
        update_media_info(screen_number, custom_body=item.dict())
    except StopIteration as e:
        pass


def verify_screen_number(screen_number: str):
    screen_number = int(screen_number)
    if type(screen_number) == int and 1 <= screen_number <= 6:
        return screen_number
    else:
        abort(404, description='Screen number is int between 1 and 6.')


if __name__ == '__main__':
    socketio.run(app=app, host=server_host, port=server_port)
