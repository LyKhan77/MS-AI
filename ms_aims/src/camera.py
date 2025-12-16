import cv2
import threading
import time

class CameraHandler:
    def __init__(self, camera_id=0, width=1280, height=720):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self.is_running = False
        self.thread = None
        self.latest_frame = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()

    def _capture_loop(self):
        print(f"Starting camera {self.camera_id}")
        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                self.latest_frame = frame
            else:
                # If reading fails, just sleep a bit to avoid CPU spin
                time.sleep(0.5)
            
            # Limit FPS slightly to save resources if needed
            time.sleep(0.01)
        
        if self.cap:
            self.cap.release()
        print("Camera released.")

    def get_frame(self):
        return self.latest_frame
