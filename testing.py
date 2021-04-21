import socketio
import time

sio = socketio.Client()


@sio.event
def message(data):
    print('I received a message!')
    print(data)


@sio.on('screen refresh')
def on_message(data):
    print('I received a message!')
    print(data)


@sio.event
def connect():
    print("I'm connected!")


@sio.event
def connect_error():
    print("The connection failed!")


@sio.event
def disconnect():
    print("I'm disconnected!")


def send_screen_number(number: int):
    data = {'screen': str(number), 'sid': sio.sid}
    sio.emit('screen number', data)


if __name__ == "__main__":
    sio.connect('http://192.168.43.111:8800')
    sio.emit('my message', {'foo': 'bar'})
    sio.emit('message', {'type': 'img'})
    sio.emit('finished playing', {'screen_number': 1})
    time.sleep(2)
    send_screen_number(1)
    # sio.disconnect()
