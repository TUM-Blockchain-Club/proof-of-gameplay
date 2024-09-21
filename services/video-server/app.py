from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import base64

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Store the latest frame
latest_frame = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/video')
def test_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/video')
def test_disconnect():
    print('Client disconnected')

@socketio.on('frame', namespace='/video')
def receive_frame(data):
    global latest_frame
    # Data is expected to be bytes
    latest_frame = base64.b64encode(data).decode('utf-8')
    # Broadcast the frame to all connected clients
    emit('update_frame', latest_frame, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
