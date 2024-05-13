import cv2
import time
from ultralytics import YOLO
from src.config import config

model = YOLO(config["model_path"])
class_name = config["class_name"]
confidence = config["confidence_threshold"]

video_capture = None
total_drops = 0
drops_in_one_minute = 0
start_time = time.time()

def detect_drops(frame):
    results = model.predict(frame)[0]
    detections = []
    for result in results.boxes:
        x1, y1, x2, y2 = result.xyxy[0]
        confidence = result.conf[0]
        class_id = result.cls[0]
        detections.append({
            'x1': int(x1), 'y1': int(y1),
            'x2': int(x2), 'y2': int(y2),
            'confidence': float(confidence),
            'class_id': int(class_id),
            'class_name': model.names[int(class_id)]
        })
    return detections

def count_total_drops(frame):
    detections = detect_drops(frame)
    return len(detections)

def process_frame(frame):
    global total_drops, drops_in_one_minute, start_time

    drop_count = count_total_drops(frame)
    total_drops += drop_count

    current_time = time.time()
    time_diff = current_time - start_time
    if time_diff >= 60:
        drops_in_one_minute = total_drops - drops_in_one_minute
        start_time = current_time

def draw_detections(frame, detections):
    for detection in detections:
        x1, y1, x2, y2 = detection['x1'], detection['y1'], detection['x2'], detection['y2']
        confidence = detection['confidence']
        class_name = detection['class_name']
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        label = f"{class_name} ({confidence:.2f})"
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (int(x1), int(y1) - label_height - 10), (int(x1) + label_width, int(y1)), (0, 255, 0), -1)
        cv2.putText(frame, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return frame