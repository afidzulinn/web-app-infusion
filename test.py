from flask import Flask, render_template, Response, stream_with_context, request, jsonify
from flask_cors import CORS
import cv2
import time
from src.camera import detect_drops, count_total_drops, draw_detections
from src.config import config

app = Flask(__name__)
CORS(app)

video_capture = None
total_drops = 0
drops_in_one_minute = 0
start_time = time.time()

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/start_camera', methods=['POST'])
def start_detection():
    global video_capture, total_drops, drops_in_one_minute, start_time
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return jsonify({"message": "Error: Unable to access the camera."}), 400

    total_drops = 0
    drops_in_one_minute = 0
    start_time = time.time()

    return jsonify({"message": "Camera and object detection started successfully."}), 200

@app.route('/video_feed')
def video_feed():
    global video_capture

    if video_capture is None:
        return jsonify({"message": "Camera is not started."}), 400

    def generate_frames():
        global video_capture
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            detections = detect_drops(frame)
            frame = draw_detections(frame, detections)

            process_frame(frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

    return Response(stream_with_context(generate_frames()), mimetype='multipart/x-mixed-replace; boundary=frame')
    # return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def process_frame(frame):
    global total_drops, drops_in_one_minute, start_time

    drop_count = count_total_drops(frame)
    total_drops += drop_count

    current_time = time.time()
    time_diff = current_time - start_time
    if time_diff >= 60:
        drops_in_one_minute = total_drops - drops_in_one_minute
        start_time = current_time

@app.route('/stop_camera', methods=['POST'])
def stop_detection():
    global video_capture

    if video_capture is not None:
        video_capture.release()
        cv2.destroyAllWindows()
        video_capture = None

    return jsonify({"message": "Object detection and camera stopped."}), 200

@app.route('/drop_stats', methods=['GET'])
def get_drop_stats():
    global total_drops, drops_in_one_minute

    return jsonify({"total_drops": total_drops,
                    "drops_in_one_minute": drops_in_one_minute}), 200

if __name__ == "__main__":
    app.run(port=config["port"], debug=True)