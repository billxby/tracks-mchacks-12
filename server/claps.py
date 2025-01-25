import cv2
import numpy as np
import time
from datetime import datetime, timedelta

# Initialize variables
cap = cv2.VideoCapture(0)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Motion detection parameters
motion_history = []
MOTION_THRESHOLD = 10000  # Adjust based on testing
CLAP_THRESHOLD = 30000    # Adjust based on testing
MOTION_HISTORY_LENGTH = 10
last_clap_time = 0
CLAP_COOLDOWN = 0.3  # Seconds between possible claps
clap_count = 0
timer_running = False
timer_start = None
current_time = "00:00:00"
warning_display = False
warning_start = None
RED_WARNING_DURATION = 2

def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=int(seconds)))

def detect_motion(frame1, frame2):
    """Detect motion between two frames"""
    # Convert frames to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Calculate absolute difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Apply threshold
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    # Apply some noise reduction
    thresh = cv2.dilate(thresh, None, iterations=2)
    thresh = cv2.erode(thresh, None, iterations=2)
    
    # Calculate total motion
    motion_score = np.sum(thresh) / 255
    
    return motion_score, thresh

# Initialize previous frame
_, prev_frame = cap.read()
prev_frame = cv2.flip(prev_frame, 1)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    
    # Detect motion
    motion_score, motion_mask = detect_motion(prev_frame, frame)
    motion_history.append(motion_score)
    
    # Keep motion history at fixed length
    if len(motion_history) > MOTION_HISTORY_LENGTH:
        motion_history.pop(0)
    
    # Detect clap pattern
    current_time_check = time.time()
    if len(motion_history) >= 3:
        # Look for sharp spike in motion
        if (motion_history[-1] > CLAP_THRESHOLD and 
            motion_history[-2] > MOTION_THRESHOLD and
            current_time_check - last_clap_time > CLAP_COOLDOWN):
            
            clap_count += 1
            last_clap_time = current_time_check
            
            # Handle three claps - show warning or close
            if clap_count == 3:
                if timer_running:
                    warning_display = True
                    warning_start = time.time()
                else:
                    break  # Exit program
                clap_count = 0
            
            #Handle two claps - toggle timer
            elif clap_count == 2:
                if not timer_running:
                    timer_start = time.time()
                    timer_running = True
                else:
                    timer_running = False
                clap_count = 0
            

    
    # Reset clap count after delay
    if current_time_check - last_clap_time > 1.5:
        clap_count = 0
    
    # Update and display timer
    if timer_running:
        elapsed_time = time.time() - timer_start
        current_time = format_time(elapsed_time)
    
    # Draw motion detection visualization
    motion_overlay = motion_mask.copy()
    motion_overlay = cv2.cvtColor(motion_overlay, cv2.COLOR_GRAY2BGR)
    frame_with_overlay = cv2.addWeighted(frame, 1, motion_overlay, 0.3, 0)
    
    # Display timer
    cv2.putText(frame_with_overlay, current_time, (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Display clap count and motion level
    cv2.putText(frame_with_overlay, f"Claps: {clap_count}", (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame_with_overlay, f"Motion: {int(motion_score)}", (50, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Handle warning display
    if warning_display:
        cv2.putText(frame_with_overlay, "WARNING!", 
                    (frame_width//2 - 100, frame_height//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        if time.time() - warning_start > RED_WARNING_DURATION:
            warning_display = False
    
    # Display frame
    cv2.imshow('Clap Timer Control', frame_with_overlay)
    
    # Update previous frame
    prev_frame = frame.copy()
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()