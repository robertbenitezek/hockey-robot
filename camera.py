import signal
import os
import cv2
import threading
from flask import Flask, Response

app = Flask(__name__)

# setup camera
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640) #width
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) #height
cam.set(cv2.CAP_PROP_FPS, 60) #camera framerate
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # minimize buffer lag

# shared frame state
latest_frame = None
frame_lock = threading.Lock() #instantiate the frame lock

#capture loop runs in background thread, continuously reading latest frame
def capture_loop():

    #declare latest frame variable as global inside 
    #of capture loop function so that it is seen everywhere
    global latest_frame 

    while True:
        success, img = cam.read() #grab frame

        #if frame grab was unsuccessful continue
        if not success: 
            continue
        
        #compress captured frame into a jpeg, keeping 60% quality
        _, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 60]) 
        
        #lock the latest_frame resource while it's being written and turn into raw bytes to send over network
        with frame_lock:
            latest_frame = encoded.tobytes()

#Create capture thread
t = threading.Thread(target=capture_loop, daemon=True)

#begin Capture Thread
t.start()

#In event of escape or program shutdown, release camera resource
def shutdown(sig, frame):
    print("\nShutting down...")
    cam.release()
    os.exit(0)

#In event of escape or program shutdown, release camera resource
signal.signal(signal.SIGINT, shutdown)

#main landing page of webserver
@app.route("/")
def index():
    return """
    <body style="background: black;">
        <div style="width: 640px; margin: 0px auto;">
            <img src="/mjpeg" />
        </div>
    </body>
    """

#gets the latest frame that has been encoded
def gather_img():
    while True:
        
        #lock the frame resource to ensure no race condition
        with frame_lock:
            
            #read from the latest frame
            frame = latest_frame

        #if not successful then it is what it is
        if frame is None:
            continue
        
        # build the multipart HTTP chunk (boundary + header + jpeg bytes) and send it,
        # then pause until Flask asks for the next frame
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#mjpeg section of webserver
@app.route("/mjpeg")
def mjpeg():
    
    # pass the generator to Flask, which pulls frames from it one at a time
    # multipart/x-mixed-replace tells browser to replace previous frame with each new one
    # boundary=frame matches the --frame delimiter in our yield
    return Response(gather_img(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 0.0.0.0 means accept connections from any network interface (not just localhost)
# threaded=True lets Flask handle multiple connections simultaneously
app.run(host='0.0.0.0', threaded=True)