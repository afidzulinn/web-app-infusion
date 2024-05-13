from flask import Flask, render_template, Response, stream_with_context, request, jsonify
from flask_cors import CORS
import cv2
import time
from src.camera import detect_drops, count_total_drops, draw_detections, process_frame
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

@app.route('/video_feed')
def video_feed():
    global video_capture, total_drops, drops_in_one_minute, start_time
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return jsonify({"message": "Error: Unable to access the camera."})

    total_drops = 0
    drops_in_one_minute = 0
    start_time = time.time()

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


@app.route('/stop_camera', methods=['POST'])
def stop_detection():
    global video_capture

    if video_capture is not None:
        video_capture.release()
        cv2.destroyAllWindows()
        video_capture = None

    return jsonify({"message": "Object detection and camera stopped."})

@app.route('/drop_stats', methods=['GET'])
def get_drop_stats():
    global total_drops, drops_in_one_minute

    return jsonify({"total_drops": total_drops,
                    "drops_in_one_minute": drops_in_one_minute})

if __name__ == "__main__":
    app.run(port=config["port"], debug=True)