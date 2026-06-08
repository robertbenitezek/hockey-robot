import cv2
import numpy as np
import sys

# ── Camera Configuration ──────────────────────────────────────────────────────
GSTREAMER_PIPELINE = (
    'v4l2src device=/dev/camera ! '
    'image/jpeg,width=640,height=480,framerate=30/1 ! '
    'nvv4l2decoder ! '
    'nvvidconv ! '
    'video/x-raw,format=BGRx ! '
    'videoconvert ! '
    'appsink'
)

# ── Blob Detection Thresholds ─────────────────────────────────────────────────
# Pixels darker than this value (0–255) are considered "black"
DARK_THRESHOLD = 60

# Minimum contour area in pixels — filters out tiny noise specks
MIN_BLOB_AREA = 500


def open_camera():
    cam = cv2.VideoCapture(GSTREAMER_PIPELINE, cv2.CAP_GSTREAMER)
    if not cam.isOpened():
        print("[ERROR] Could not open camera via GStreamer.")
        print("        Check that /dev/camera exists and the pipeline is correct.")
        sys.exit(1)
    print("[INFO] Camera opened successfully.")
    return cam


def find_black_blobs(frame):
    """
    Returns a list of bounding boxes (x, y, w, h) for black blobs found in frame.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Threshold: pixels darker than DARK_THRESHOLD become white (255),
    # everything else becomes black (0) — i.e. THRESH_BINARY_INV
    _, mask = cv2.threshold(gray, DARK_THRESHOLD, 255, cv2.THRESH_BINARY_INV)

    # Optional: clean up noise with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours of white regions (our "black blobs")
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= MIN_BLOB_AREA:
            boxes.append(cv2.boundingRect(cnt))   # (x, y, w, h)

    return boxes, mask


def draw_boxes(frame, boxes):
    """Draw a green bounding box and label for each detected blob."""
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        label = f"Blob {i + 1}  [{w}x{h}]"
        label_y = y - 10 if y - 10 > 10 else y + 20
        cv2.putText(
            frame, label,
            (x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (0, 255, 0), 2,
        )
    return frame


def main():
    cam = open_camera()

    print("[INFO] Press 'q' to quit | 'd' to toggle debug mask view")
    show_mask = False

    while True:
        ret, frame = cam.read()
        if not ret:
            print("[WARNING] Failed to grab frame — retrying...")
            continue

        boxes, mask = find_black_blobs(frame)
        annotated = draw_boxes(frame.copy(), boxes)

        # Status overlay
        status = f"Blobs detected: {len(boxes)}"
        cv2.putText(annotated, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

        # Show either the annotated colour frame or the binary mask
        display = mask if show_mask else annotated
        window_title = "Blob Detection (mask)" if show_mask else "Blob Detection"
        cv2.imshow(window_title, display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("[INFO] Quitting.")
            break
        elif key == ord('d'):
            show_mask = not show_mask
            cv2.destroyAllWindows()   # close old window so title updates

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
