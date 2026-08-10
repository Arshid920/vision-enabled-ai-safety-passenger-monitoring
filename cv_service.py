import cv2
import numpy as np
import threading
import time
import math
import cvzone
from pathlib import Path

# ================================
# CONFIGURATION
# ================================
MAX_CAPACITY = 5
LEFT_BORDER = 100
RIGHT_BORDER = 920
FRAME_W = 1020
FRAME_H = 600

# Fix 1: Ensure YOLO model path looks at the root ml_project folder
MODEL_PATH = str(Path(__file__).resolve().parents[2] / "yolov8s.pt")

MIN_BOX_W = 0
MIN_BOX_H = 0

CAMERA_START_IDX = 0


# ================================
# PLACEHOLDER GENERATOR
# ================================
# Fix 2: Creating a fallback JPEG image so the browser stream never hangs.
# If the browser receives nothing, the dashboard gets completely stuck waiting.
def _get_placeholder_jpeg(msg="Camera starting..."):
    img = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
    img[:] = (20, 20, 30)
    cv2.putText(img, msg, (100, FRAME_H // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (150, 150, 150), 2)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ================================
# TRACKER
# ================================
class Tracker:
    def __init__(self):
        self.center_points = {}
        self.id_count = 0
        self.distance_threshold = 50   # matching tracker.py

    def update(self, objects_rect):
        objects_bbs_ids = []

        for rect in objects_rect:
            x1, y1, x2, y2 = rect
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            same_object_detected = False

            for object_id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < self.distance_threshold:
                    self.center_points[object_id] = (cx, cy)
                    objects_bbs_ids.append([x1, y1, x2, y2, object_id])
                    same_object_detected = True
                    break

            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x1, y1, x2, y2, self.id_count])
                self.id_count += 1

        # Clean unused IDs
        new_center_points = {}
        for obj_bb_id in objects_bbs_ids:
            _, _, _, _, object_id = obj_bb_id
            new_center_points[object_id] = self.center_points[object_id]

        self.center_points = new_center_points.copy()

        return objects_bbs_ids


# ================================
# GLOBAL STATE
# ================================
_lock = threading.Lock()

# Start with a placeholder instead of an empty byte string
_latest_frame = _get_placeholder_jpeg("Initializing AI Model...")

_status = {
    "people_count": 0,
    "overcrowded": False,
    "stepped_out": False,
    "out_of_bounds_count": 0,
    "life_jacket_ok": False,
    "life_jacket_worn": 0,
    "life_jacket_not_worn": 0,
    "camera_ok": False,
}

_thread = None
_running = False


# ================================
# OVERLAP CHECK (IoM - Intersection over Minimum)
# ================================
def _calculate_overlap(box1, box2):
    x1, y1, x2, y2 = box1
    jx1, jy1, jx2, jy2 = box2
    
    ix1, iy1 = max(x1, jx1), max(y1, jy1)
    ix2, iy2 = min(x2, jx2), min(y2, jy2)
    inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (jx2 - jx1) * (jy2 - jy1)
    
    min_area = min(box1_area, box2_area)
    if min_area == 0:
        return 0.0
        
    return inter_area / min_area


# ================================
# OUT OF BOAT CHECK (HALF BODY)
# ================================
def _is_out_of_bounds(x1, x2):

    box_width = x2 - x1

    if x1 < LEFT_BORDER:
        outside = LEFT_BORDER - x1
        if outside > box_width * 0.30:
            return True

    if x2 > RIGHT_BORDER:
        outside = x2 - RIGHT_BORDER
        if outside > box_width * 0.30:
            return True

    return False


# ================================
# VIDEO CAPTURE THREAD (ZERO LAG)
# ================================
class VideoCaptureThread:
    def __init__(self, start_idx=0):
        self.cap = None
        self.ret = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        self.start_idx = start_idx
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.running:
            if self.cap is None:
                for idx in range(self.start_idx, self.start_idx + 3):
                    test_cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                    if test_cap.isOpened():
                        ret, frame = test_cap.read()
                        if ret:
                            self.cap = test_cap
                            with self.lock:
                                self.ret = ret
                                self.frame = frame
                            break
                        test_cap.release()
                    else:
                        test_cap.release()
                if self.cap is None:
                    time.sleep(2)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                with self.lock:
                    self.ret = False
            else:
                with self.lock:
                    self.ret = ret
                    self.frame = frame

    def read(self):
        with self.lock:
            return self.ret, (self.frame.copy() if self.frame is not None else None)

    def release(self):
        self.running = False
        if self.cap:
            self.cap.release()

# ================================
# CAPTURE LOOP
# ================================
def _capture_loop():

    global _latest_frame, _status, _running

    from ultralytics import YOLO

    try:
        model = YOLO(MODEL_PATH)
        class_names = model.names
    except Exception as e:
        print(f"Failed to load YOLO: {e}")
        return

    tracker = Tracker()

    cam_thread = VideoCaptureThread(CAMERA_START_IDX)
    
    while _running:
        ret, frame = cam_thread.read()

        if not ret or frame is None:
            with _lock:
                _status["camera_ok"] = False
                _latest_frame = _get_placeholder_jpeg("No camera found. Retrying in 1s...")
            time.sleep(1)
            continue
        else:
            with _lock:
                _status["camera_ok"] = True

        frame = cv2.resize(frame, (FRAME_W, FRAME_H))

        cv2.line(frame, (LEFT_BORDER,0),(LEFT_BORDER,FRAME_H),(0,255,255),2)
        cv2.line(frame, (RIGHT_BORDER,0),(RIGHT_BORDER,FRAME_H),(0,255,255),2)

        results = model.predict(frame, conf=0.5, verbose=False)

        raw_boxes = []
        life_jacket_boxes = []

        for det in results[0].boxes.data:

            x1,y1,x2,y2,conf,cls = det
            label = class_names[int(cls)]

            x1,y1,x2,y2 = int(x1),int(y1),int(x2),int(y2)

            if label == "person":
                raw_boxes.append([x1,y1,x2,y2])

            elif label == "life jacket":
                life_jacket_boxes.append([x1,y1,x2,y2])

        # Tracking matches basic tracker.py perfectly
        boxes_ids = tracker.update(raw_boxes)

        total_people = len(boxes_ids)

        passenger_count = 0
        out_of_bounds_count = 0
        life_jacket_worn = 0
        stepped_out = False

        for box_id in boxes_ids:

            x1,y1,x2,y2,obj_id = box_id
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # 1. Boundary logic using center point
            if cx < LEFT_BORDER or cx > RIGHT_BORDER:
                stepped_out = True
                out_of_bounds_count += 1
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),2)
                cv2.putText(frame,"OUT OF BOAT",
                    (x1,y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,(0,0,255),2)
            else:
                passenger_count += 1
                
            # 2. Life jacket overlap check (IoU/IoM > 0.3)
            person_has_jacket = False
            person_box = [x1, y1, x2, y2]
            
            for j_box in life_jacket_boxes:
                if _calculate_overlap(person_box, j_box) > 0.3:
                    person_has_jacket = True
                    break
                    
            if person_has_jacket:
                life_jacket_worn += 1

        if out_of_bounds_count>0:

            cv2.putText(frame,f"OUT OF BOAT: {out_of_bounds_count}",
                (10,95),  # Shifted down slightly to make room for people count
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,(0,0,255),3)

        # The "People: X" overlay has been removed to reduce clutter,
        # as the passenger count is already displayed on the Dashboard UI.

        overcrowded = passenger_count > MAX_CAPACITY
        
        # Enforce strict UI constraints requested: exactly match passenger_count
        life_jacket_worn = min(life_jacket_worn, passenger_count)
        life_jacket_not_worn = max(0, passenger_count - life_jacket_worn)

        _,buffer = cv2.imencode(".jpg",frame)
        jpeg = buffer.tobytes()

        with _lock:

            _latest_frame = jpeg

            _status.update({
                "people_count": passenger_count,
                "total_people": total_people,
                "overcrowded": overcrowded,
                "stepped_out": stepped_out,
                "out_of_bounds_count": out_of_bounds_count,
                "life_jacket_ok": (life_jacket_not_worn == 0 and passenger_count > 0) if passenger_count > 0 else True,
                "life_jacket_worn": life_jacket_worn,
                "life_jacket_not_worn": life_jacket_not_worn,
                "camera_ok": True
            })

    cam_thread.release()


# ================================
# API FUNCTIONS
# ================================
def start():

    global _thread,_running

    if _thread and _thread.is_alive():
        return

    _running = True
    _thread = threading.Thread(target=_capture_loop,daemon=True)
    _thread.start()


def stop():
    global _running
    _running=False


def get_status():

    with _lock:
        return dict(_status)


def generate_frames():

    while True:

        with _lock:
            frame=_latest_frame

        if frame:

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"+frame+b"\r\n"
            )

        time.sleep(0.01)
