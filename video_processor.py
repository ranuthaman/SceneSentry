
from pathlib import Path

import cv2
from ultralytics import YOLO


# Load the pretrained model once, when this module is initialized.
MODEL_NAME = "yolov8n.pt"


def process_video(video_path, confidence=0.35, frame_stride=2):
    """
    Detect objects in a video and return structured detection records.

    Args:
        video_path: Path to the input video.
        confidence: Minimum confidence threshold for detections.
        frame_stride: Process every Nth frame.

    Returns:
        A list of dictionaries containing timestamps, labels,
        confidence scores, and bounding-box coordinates.
    """
    video_path = Path(video_path)

    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if frame_stride < 1:
        raise ValueError("frame_stride must be at least 1")

    model = YOLO(MODEL_NAME)
    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        capture.release()
        raise ValueError("Could not determine the video's frame rate")

    detections = []
    frame_index = 0

    try:
        while True:
            success, frame = capture.read()

            if not success:
                break

            if frame_index % frame_stride == 0:
                result = model.predict(
                    frame,
                    conf=confidence,
                    imgsz=640,
                    verbose=False
                )[0]

                timestamp = frame_index / fps

                for box in result.boxes:
                    class_id = int(box.cls[0])

                    detections.append({
                        "timestamp": round(timestamp, 3),
                        "object": model.names[class_id],
                        "confidence": round(float(box.conf[0]), 3),
                        "x1": int(box.xyxy[0][0]),
                        "y1": int(box.xyxy[0][1]),
                        "x2": int(box.xyxy[0][2]),
                        "y2": int(box.xyxy[0][3])
                    })

            frame_index += 1

    finally:
        capture.release()

    return detections
