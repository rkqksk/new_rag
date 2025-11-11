#!/usr/bin/env python3
"""
Camera Server for Raspberry Pi

Serves camera frames via HTTP API for manufacturing system
Supports: USB cameras, Pi Camera Module (v2/v3)

Usage:
    python camera_server.py --port 5000 --fps 30
"""

import argparse
import logging
from flask import Flask, Response, jsonify
import cv2
import time
from threading import Lock
import io
from datetime import datetime

# Try to import picamera2 for Pi Camera Module
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global camera object
camera = None
camera_lock = Lock()
frame_count = 0
fps = 0


class CameraServer:
    """Camera server for Raspberry Pi"""

    def __init__(self, camera_type="usb", device_id=0, resolution=(640, 480), fps=30):
        """
        Initialize camera server

        Args:
            camera_type: "usb" or "picamera"
            device_id: Camera device ID (0, 1, etc.)
            resolution: (width, height)
            fps: Frames per second
        """
        self.camera_type = camera_type
        self.device_id = device_id
        self.resolution = resolution
        self.target_fps = fps
        self.camera = None
        self.last_frame = None
        self.frame_time = 0

    def start(self):
        """Start camera"""
        if self.camera_type == "picamera":
            if not PICAMERA_AVAILABLE:
                logger.error("picamera2 not installed. Install with: pip install picamera2")
                logger.info("Falling back to USB camera...")
                self.camera_type = "usb"
            else:
                logger.info("Starting Pi Camera Module...")
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(
                    main={"size": self.resolution}
                )
                self.camera.configure(config)
                self.camera.start()
                logger.info(f"Pi Camera started at {self.resolution}")
                return

        # USB Camera
        logger.info(f"Starting USB camera {self.device_id}...")
        self.camera = cv2.VideoCapture(self.device_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.camera.set(cv2.CAP_PROP_FPS, self.target_fps)

        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera {self.device_id}")

        logger.info(f"USB camera started at {self.resolution}")

    def capture_frame(self):
        """Capture single frame"""
        if self.camera_type == "picamera":
            # Pi Camera
            frame = self.camera.capture_array()
            # Convert RGB to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            # USB Camera
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture frame")
                return None

        self.last_frame = frame
        self.frame_time = time.time()
        return frame

    def get_jpeg(self):
        """Get frame as JPEG bytes"""
        frame = self.capture_frame()
        if frame is None:
            return None

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            return None

        return buffer.tobytes()

    def stop(self):
        """Stop camera"""
        if self.camera:
            if self.camera_type == "picamera":
                self.camera.stop()
            else:
                self.camera.release()
            logger.info("Camera stopped")


# Global camera server
camera_server = None


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "camera_type": camera_server.camera_type if camera_server else "not initialized",
        "fps": fps,
        "frame_count": frame_count,
        "last_capture": camera_server.frame_time if camera_server else None
    })


@app.route('/capture')
def capture():
    """Capture single frame (JPEG)"""
    if not camera_server:
        return jsonify({"error": "Camera not initialized"}), 500

    try:
        jpeg_bytes = camera_server.get_jpeg()
        if jpeg_bytes is None:
            return jsonify({"error": "Failed to capture frame"}), 500

        global frame_count
        frame_count += 1

        return Response(
            jpeg_bytes,
            mimetype='image/jpeg',
            headers={'X-Frame-Count': str(frame_count)}
        )
    except Exception as e:
        logger.error(f"Capture error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/stream')
def stream():
    """Stream video (MJPEG)"""
    def generate():
        """Generate MJPEG stream"""
        global frame_count, fps
        last_fps_time = time.time()
        fps_counter = 0

        while True:
            try:
                jpeg_bytes = camera_server.get_jpeg()
                if jpeg_bytes is None:
                    time.sleep(0.1)
                    continue

                # Update FPS
                fps_counter += 1
                now = time.time()
                if now - last_fps_time >= 1.0:
                    fps = fps_counter
                    fps_counter = 0
                    last_fps_time = now

                frame_count += 1

                # Yield as MJPEG
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')

                # Frame rate limiting
                time.sleep(1.0 / camera_server.target_fps)

            except Exception as e:
                logger.error(f"Stream error: {e}")
                break

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/info')
def info():
    """Camera information"""
    if not camera_server:
        return jsonify({"error": "Camera not initialized"}), 500

    return jsonify({
        "camera_type": camera_server.camera_type,
        "device_id": camera_server.device_id,
        "resolution": camera_server.resolution,
        "target_fps": camera_server.target_fps,
        "actual_fps": fps,
        "frame_count": frame_count,
        "uptime_seconds": time.time() - start_time if 'start_time' in globals() else 0
    })


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Camera server for Raspberry Pi")
    parser.add_argument("--camera-type", default="usb", choices=["usb", "picamera"],
                        help="Camera type (usb or picamera)")
    parser.add_argument("--device", type=int, default=0,
                        help="Camera device ID (for USB cameras)")
    parser.add_argument("--resolution", default="640x480",
                        help="Resolution (WIDTHxHEIGHT)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Target FPS")
    parser.add_argument("--port", type=int, default=5000,
                        help="Server port")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Server host")

    args = parser.parse_args()

    # Parse resolution
    width, height = map(int, args.resolution.split('x'))

    # Initialize camera server
    global camera_server, start_time
    camera_server = CameraServer(
        camera_type=args.camera_type,
        device_id=args.device,
        resolution=(width, height),
        fps=args.fps
    )

    try:
        camera_server.start()
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("Camera Server Started")
        logger.info("=" * 60)
        logger.info(f"Camera Type: {camera_server.camera_type}")
        logger.info(f"Resolution: {width}x{height}")
        logger.info(f"Target FPS: {args.fps}")
        logger.info(f"Server: http://{args.host}:{args.port}")
        logger.info("")
        logger.info("Endpoints:")
        logger.info(f"  Health:  http://{args.host}:{args.port}/health")
        logger.info(f"  Capture: http://{args.host}:{args.port}/capture")
        logger.info(f"  Stream:  http://{args.host}:{args.port}/stream")
        logger.info(f"  Info:    http://{args.host}:{args.port}/info")
        logger.info("=" * 60)

        # Start Flask server
        app.run(host=args.host, port=args.port, threaded=True)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if camera_server:
            camera_server.stop()


if __name__ == "__main__":
    main()
