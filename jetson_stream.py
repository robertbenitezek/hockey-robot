import cv2
import socket
import struct

cam = cv2.VideoCapture(
    'v4l2src device=/dev/camera ! image/jpeg,width=640,height=480,framerate=30/1 ! nvv4l2decoder ! nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! appsink sync=false',
    cv2.CAP_GSTREAMER
)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 5000))
server.listen(1)
print("Waiting for connection...")
conn, addr = server.accept()
print(f"Connected: {addr}")

while True:
    success, frame = cam.read()
    if not success:
        continue

    # your CV processing here
    _, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    data = jpg.tobytes()

    # send length prefix then data
    conn.sendall(struct.pack('>L', len(data)) + data)
