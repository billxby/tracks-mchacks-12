import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

FACE_WIDTH = 12
min_pos = float('inf')
max_pos = float('-inf')
# Initialize variables
prev_wrist_y = None
curl_velocities = []
max_velocity = 0
velocity_threshold = 0.1  # Threshold for detecting slowdown
window_size = 5  # For smoothing velocity readings

# Get screen dimensions
try:
    screen = get_monitors()[0]
    SCREEN_HEIGHT = screen.height
except:
    SCREEN_HEIGHT = 1080  # fallback height if can't detect screen

def calculate_smoothed_velocity(velocities, window_size):
    if len(velocities) < window_size:
        return sum(velocities) / len(velocities)
    return sum(velocities[-window_size:]) / window_size

# Open video capture
cap = cv2.VideoCapture(1)

# Get original video dimensions
original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
aspect_ratio = original_width / original_height

# Calculate new dimensions to maximize height while maintaining aspect ratio
new_height = min(SCREEN_HEIGHT - 100, 1920)  # Leave some margin for taskbar and window chrome
new_width = int(new_height * aspect_ratio)

# Set window properties
cv2.namedWindow("Bicep Curl Velocity Tracker", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Bicep Curl Velocity Tracker", new_width, new_height)

prev_time = time.time()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Resize frame to new dimensions
    frame = cv2.resize(frame, (new_width, new_height))
    
    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process pose
    results = pose.process(rgb_frame)
    current_time = time.time()
    dt = current_time - prev_time
    fps = 1 / dt
    prev_time = current_time

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # Get wrist and shoulder landmarks for curl tracking
        landmarks = results.pose_landmarks.landmark
        wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        
        right_shoulder_x, right_shoulder_y = right_shoulder.x * new_width, right_shoulder.y * new_height
        left_shoulder_x, left_shoulder_y = left_shoulder.x * new_width, left_shoulder.y * new_height
        
        right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value]
        left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]

        right_ear_x, right_ear_y = right_ear.x * new_width, right_ear.y * new_height
        left_ear_x, left_ear_y = left_ear.x * new_width, left_ear.y * new_height
        
        propConstant = FACE_WIDTH / (((right_ear_y - left_ear_y) ** 2 + (right_ear_x - left_ear_x) ** 2) ** 0.5)
        min_pos = min(min_pos, right_shoulder_y * propConstant)
        max_pos = max(max_pos, right_shoulder_y * propConstant)

        print(min_pos, max_pos)
        
        shoulder_width = (((right_shoulder_y - left_shoulder_y) ** 2 + (right_shoulder_x - left_shoulder_x) ** 2) ** 0.5)
        # Calculate wrist position relative to shoulder
        wrist_y = (shoulder.y - wrist.y) * frame.shape[0]
        
        # Calculate velocity
        if prev_wrist_y is not None:
            velocity = abs(wrist_y - prev_wrist_y) / dt
            curl_velocities.append(velocity)
            
            # Calculate smoothed velocity
            smoothed_velocity = calculate_smoothed_velocity(curl_velocities, window_size)
            
            # Update max velocity
            max_velocity = max(max_velocity, smoothed_velocity)
            
            # Scale font and UI elements based on window height
            font_scale = new_height / 720  # Base scale on 720p reference
            thickness = max(1, int(font_scale * 2))
            
            # Display velocity information with scaled font
            velocity_text = f"Curl Speed: {smoothed_velocity:.1f} pixels/sec"
            cv2.putText(frame, velocity_text, (int(30 * font_scale), int(50 * font_scale)), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            cv2.putText(frame, str(propConstant), (int(30 * font_scale), int(250 * font_scale)), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            cv2.putText(frame, str(propConstant * shoulder_width), (int(30 * font_scale), int(300 * font_scale)), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
        
            
            # Display percentage of max speed
            if max_velocity > 0:
                speed_percentage = (smoothed_velocity / max_velocity) * 100
                percentage_text = f"Percentage of Max Speed: {speed_percentage:.1f}%"
                cv2.putText(frame, percentage_text, (int(30 * font_scale), int(100 * font_scale)),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
            
            # Check for slowdown
            if smoothed_velocity < velocity_threshold * max_velocity:
                cv2.putText(frame, "WARNING: Slowing Down!", (int(30 * font_scale), int(150 * font_scale)),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
            
            # Draw velocity bar (scaled)
            bar_max_width = int(400 * font_scale)
            bar_height = int(40 * font_scale)
            bar_y = int(180 * font_scale)
            bar_width = int((smoothed_velocity / max_velocity) * bar_max_width) if max_velocity > 0 else 0
            cv2.rectangle(frame, (30, bar_y), (30 + bar_max_width, bar_y + bar_height), (0, 0, 0), thickness)
            cv2.rectangle(frame, (30, bar_y), (30 + bar_width, bar_y + bar_height), (0, 255, 0), -1)

        prev_wrist_y = wrist_y

    # Display frame
    cv2.imshow("Bicep Curl Velocity Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()