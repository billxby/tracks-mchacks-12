import cv2
import time

class Chronometer:
    def __init__(self):
        self.start_time = None
        self.running = False
        self.elapsed_time = 0

    def start(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True

    def stop(self):
        if self.running:
            self.elapsed_time += time.time() - self.start_time
            self.running = False

    def reset(self):
        self.start_time = None
        self.running = False
        self.elapsed_time = 0

    def get_time(self):
        if self.running:
            return self.elapsed_time + (time.time() - self.start_time)
        return self.elapsed_time

def main():
    # Initialize video capture
    cap = cv2.VideoCapture(1)
    
    # Create chronometer
    chrono = Chronometer()
    
    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip frame
        frame = cv2.flip(frame, 1)
        
        # Display chronometer
        time_text = f"Time: {chrono.get_time():.2f} sec"
        cv2.putText(frame, time_text, (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Key event handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):  # Start/Stop
            if chrono.running:
                chrono.stop()
            else:
                chrono.start()
        elif key == ord('r'):  # Reset
            chrono.reset()
        elif key == ord('q'):  # Quit
            break
        
        # Show frame
        cv2.imshow("Chronometer", frame)
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()


main()