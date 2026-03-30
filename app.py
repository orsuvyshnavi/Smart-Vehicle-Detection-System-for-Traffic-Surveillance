import torch
from flask import Flask, render_template, Response, jsonify, request, send_file
import cv2
import numpy as np
from ultralytics import YOLO
import time
import json
import os
from datetime import datetime
import threading
import queue
import logging
from collections import defaultdict, deque
import sqlite3
from tracker import VehicleTracker

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'vehicle-recognition-project-2024'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
model = None
camera = None
detection_stats = {
    'total_vehicles': 0,
    'vehicle_types': defaultdict(int),
    'processing_times': deque(maxlen=100),
    'fps_history': deque(maxlen=100),
    'weather_conditions': defaultdict(int),
    'detection_confidence': deque(maxlen=100)
}

# Weather simulation effects
WEATHER_CONDITIONS = {
    'normal': 'Clear Conditions',
    'rain': 'Rainy Weather',
    'fog': 'Foggy Conditions',
    'night': 'Low Light/Night',
    'snow': 'Snowy Weather'
}

def initialize_model():
    """Initialize YOLO model for vehicle detection"""
    global model
    try:
        # Initialize the VehicleTracker wrapper
        model = VehicleTracker()
        logger.info("VehicleTracker initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

def detect_vehicles(frame, weather_type='normal'):
    """
    Wrapper for VehicleTracker - handles detection and tracking
    Returns: annotated_frame, list_of_dicts, processing_time, fps
    """
    global model, detection_stats
    
    if model is None:
        model = VehicleTracker()
    
    start = time.time()
    # Tracker now returns already-annotated frame!
    annotated, detections = model.update(frame, weather_type)
    processing_time = time.time() - start
    fps = 1.0 / processing_time if processing_time > 0 else 0
    
    # Update global stats 
    detection_stats['processing_times'].append(processing_time)
    detection_stats['fps_history'].append(fps)
    detection_stats['weather_conditions'][weather_type] += len(detections)
    
    # Update vehicle type counts and confidence
    for det in detections:
        class_name = det['class_name']
        detection_stats['vehicle_types'][class_name] += 1
        detection_stats['detection_confidence'].append(det['confidence'])
    
    return annotated, detections, processing_time, fps

def generate_frames(source='camera', weather_type='normal'):
    """Generate frames for video streaming"""
    global camera
    
    try:
        if source == 'camera':
            camera = cv2.VideoCapture(0)
        else:
            # Use sample video for demonstration
            sample_video = 'hehe.mp4'
            if os.path.exists(sample_video):
                camera = cv2.VideoCapture(sample_video)
            else:
                # Fallback to camera if no video available
                logger.warning(f"Sample video {sample_video} not found, using camera")
                camera = cv2.VideoCapture(0)
        
        if not camera.isOpened():
            logger.error("Failed to open camera/video source")
            return
        
        while True:
            success, frame = camera.read()
            if not success:
                # If video ends, loop it
                if source != 'camera' and os.path.exists('sample_traffic.mp4'):
                    camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            
            # Resize frame for processing
            frame = cv2.resize(frame, (640, 480))
            
            # Detect vehicles (tracker already annotates the frame - NO NEED to draw again!)
            processed_frame, detections, processing_time, fps = detect_vehicles(frame, weather_type)
            
            # Add performance info overlay on top
            avg_fps = np.mean(detection_stats['fps_history']) if detection_stats['fps_history'] else 0
            total_vehicles = sum(detection_stats['vehicle_types'].values())
            
            # Create info text overlay
            info_text = f"FPS: {avg_fps:.1f} | Total: {total_vehicles} | Weather: {WEATHER_CONDITIONS[weather_type]}"
            
            # Add semi-transparent background for text
            overlay = processed_frame.copy()
            cv2.rectangle(overlay, (5, 5), (635, 40), (0, 0, 0), -1)
            processed_frame = cv2.addWeighted(overlay, 0.5, processed_frame, 0.5, 0)
            
            # Add text
            cv2.putText(processed_frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    except Exception as e:
        logger.error(f"Error in generate_frames: {e}")
    finally:
        if camera is not None:
            camera.release()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/video_feed/<source>/<weather>')
def video_feed(source, weather):
    """Video streaming route"""
    return Response(generate_frames(source, weather),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
@app.route('/stats')
def get_stats():
    """Get real-time statistics"""
    global detection_stats
    
    if not detection_stats['processing_times']:
        return jsonify({'status': 'no_data'})
    
    # Use tracker's lifetime counts for vehicle totals (accurate)
    # Use detection_stats for FPS/processing metrics (still valid)
    stats = {
        'total_vehicles': sum(model.lifetime.values()) if model and hasattr(model, 'lifetime') else 0,
        'vehicle_types': dict(model.lifetime) if model and hasattr(model, 'lifetime') else {},
        'avg_processing_time': float(np.mean(detection_stats['processing_times'])),
        'avg_fps': float(np.mean(detection_stats['fps_history'])),
        'avg_confidence': float(np.mean(detection_stats['detection_confidence'])) if detection_stats['detection_confidence'] else 0,
        'weather_distribution': dict(detection_stats['weather_conditions']),
        'status': 'active'
    }
    
    return jsonify(stats)


@app.route('/reset_stats')
def reset_stats():
    """Reset detection statistics"""
    global detection_stats, model
    
    detection_stats = {
        'total_vehicles': 0,
        'vehicle_types': defaultdict(int),
        'processing_times': deque(maxlen=100),
        'fps_history': deque(maxlen=100),
        'weather_conditions': defaultdict(int),
        'detection_confidence': deque(maxlen=100)
    }
    
    # Reset tracker lifetime stats
    if model and hasattr(model, 'lifetime'):
        model.lifetime.clear()
        model._seen.clear()
    
    return jsonify({'status': 'reset_complete'})

@app.route('/export_data')
def export_data():
    """Export detection data"""
    global detection_stats
    
    # Get accurate unique counts from tracker
    lifetime_counts = dict(model.lifetime) if model and hasattr(model, 'lifetime') else {}
    total_unique = sum(lifetime_counts.values())
    
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'total_vehicles': total_unique,  # Unique vehicles only
        'vehicle_types': lifetime_counts,  # Unique per class
        # Replace weather_conditions line
        'weather_conditions': {k: dict(v) for k,v in model.weather_counts.items()} if model and hasattr(model, 'weather_counts') else {},
        'performance_metrics': {
            'avg_processing_time': float(np.mean(detection_stats['processing_times'])),
            'avg_fps': float(np.mean(detection_stats['fps_history'])),
            'avg_confidence': float(np.mean(detection_stats['detection_confidence'])) if detection_stats['detection_confidence'] else 0
        },
        'methodology': 'Counts represent unique tracked vehicles, not per-frame detections'
    }
    
    return jsonify(export_data)

if __name__ == '__main__':
    # Initialize model
    if initialize_model():
        logger.info("Starting Vehicle Recognition System...")
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    else:
        logger.error("Failed to initialize system. Exiting...")