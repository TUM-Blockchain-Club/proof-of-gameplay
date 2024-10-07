from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO
import base64
import numpy as np

app = Flask(__name__)

# ML model load function
def load_model():
    # Load your model here (e.g., TensorFlow, PyTorch, etc.)
    pass

model = load_model()

# process one video frame
def process_frame(frame_data):
    image_data = base64.b64decode(frame_data.split(',')[1])
    image = Image.open(BytesIO(image_data))
    
    image_np = np.array(image)

    # predictions = model.predict(image_np)

    return {}

@app.route('/process_frame', methods=['POST'])
def process_frame_route():
    data = request.get_json()
    frame = data['frame']
    result = process_frame(frame)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='localhost', port="5050")
