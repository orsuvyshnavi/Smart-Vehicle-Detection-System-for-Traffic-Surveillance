# tracker.py - STANDARD IMPLEMENTATION
import cv2
import numpy as np
import torch
from collections import Counter
from ultralytics import YOLO

class VehicleTracker:
    """
    Standard vehicle tracking implementation using Ultralytics YOLO built-in tracking.
    This is how it's done in real projects and research papers (2023-2024).
    """
    def __init__(self, model_path="yolov26s.pt"):
        self.model = YOLO(model_path)
        self.lifetime = Counter()
        self._seen = {}

    def update(self, frame, weather_type='normal'):
        """
        Standard tracking method using YOLO's built-in track() function.
        This is the CORRECT approach used in research and production systems.
        """
        # 1. Apply weather effect first
        if weather_type != 'normal':
            frame = self.apply_weather(frame, weather_type)

        # 2. Use YOLO's built-in tracking - THIS IS THE STANDARD WAY
        # The track() method handles detection + tracking internally
        results = self.model.track(
            frame,
            conf=0.45,
            iou=0.45,
            persist=True,  # CRITICAL: Maintains track IDs across frames
            tracker="bytetrack.yaml",  # Uses ByteTrack algorithm
            verbose=False,
            classes=[2, 3, 5, 7, 1, 0]  # car, motorcycle, bus, truck, bicycle, person
        )
        
        # 3. Check if we got valid results
        if not results or len(results) == 0:
            return frame, []
        
        result = results[0]
        
        # 4. Get annotated frame (YOLO does the drawing for us!)
        annotated_frame = result.plot()
        
        # 5. Extract detection information
        detections = []
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            
            # Get box data as numpy arrays
            if hasattr(boxes, 'xyxy'):
                xyxy = boxes.xyxy.cpu().numpy() if torch.is_tensor(boxes.xyxy) else np.array(boxes.xyxy)
                conf = boxes.conf.cpu().numpy() if torch.is_tensor(boxes.conf) else np.array(boxes.conf)
                cls = boxes.cls.cpu().numpy() if torch.is_tensor(boxes.cls) else np.array(boxes.cls)
                
                # Get track IDs (this is what makes tracking work!)
                if hasattr(boxes, 'id') and boxes.id is not None:
                    ids = boxes.id.cpu().numpy() if torch.is_tensor(boxes.id) else np.array(boxes.id)
                else:
                    ids = np.arange(len(boxes))  # Fallback
                
                # Build detection list
                for i in range(len(xyxy)):
                    x1, y1, x2, y2 = xyxy[i]
                    confidence = float(conf[i])
                    class_id = int(cls[i])
                    class_name = self.model.names[class_id]
                    track_id = int(ids[i])
                    
                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence,
                        'class_name': class_name,
                        'id': track_id
                    })
                    
                    # Track lifetime unique vehicles
                    if track_id not in self._seen:
                        self._seen[track_id] = class_name
                        self.lifetime[class_name] += 1
                        # NEW: store weather count in a plain dict of Counters
                        self.weather_counts = getattr(self, 'weather_counts', {})
                        self.weather_counts.setdefault(weather_type, Counter())[class_name] += 1

        
        return annotated_frame, detections

    def apply_weather(self, frame, weather_type):
        """Apply weather simulation effects"""
        if weather_type == 'rain':
            rain_overlay = np.random.randint(0, 255, frame.shape, dtype=np.uint8)
            mask = np.random.random(frame.shape[:2]) < 0.1
            frame[mask] = cv2.addWeighted(frame[mask], 0.7, rain_overlay[mask], 0.3, 0)
        
        elif weather_type == 'fog':
            fog_color = np.full_like(frame, 200)
            frame = cv2.addWeighted(frame, 0.4, fog_color, 0.6, 0)
        
        elif weather_type == 'night':
            frame = cv2.convertScaleAbs(frame, alpha=0.4, beta=30)
        
        elif weather_type == 'snow':
            snow_overlay = np.random.randint(200, 255, frame.shape, dtype=np.uint8)
            mask = np.random.random(frame.shape[:2]) < 0.05
            frame[mask] = cv2.addWeighted(frame[mask], 0.8, snow_overlay[mask], 0.2, 0)
        
        return frame