import time
import signal
import sys
import cv2
from flask import Flask, Response

app = Flask(__name__)

# setup camera and resolution
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def shutdown(sig, frame):
    print("\nShutting down webcam and server...")
    cam.release()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)  # handles Ctrl+C

@app.route("/")
def hello_world():
    return """
    <body style="background: black;">
        <div style="width: 240px; margin: 0px auto;">
            <img src="/mjpeg" />
        </div>
    </body>
    """

def gather_img():
    while True:
        time.sleep(0.01)
        success, img = cam.read()
        if not success:
            break
        _, frame = cv2.imencode('.jpg', img)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')

@app.route("/mjpeg")
def mjpeg():
    return Response(gather_img(), mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host='0.0.0.0', threaded=True)