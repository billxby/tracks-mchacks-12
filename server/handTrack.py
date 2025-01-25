import cv2
import mediapipe as mp

def fingers_up(hand_landmarks, handedness):
    """Detect the number of fingers raised for a given hand."""
    tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky fingertips
    count = 0

    # Thumb: Check if it's open (different for left/right hand)
    if handedness == "Right":
        if hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 1].x:
            count += 1
    else:  # Left hand
        if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x:
            count += 1

    # Other fingers: Check if the tip is above the PIP joint
    for tip in tips[1:]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1

    return count

def main():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    
    # Initialize MediaPipe Hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Flip the frame horizontally for a mirrored view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert the frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        if result.multi_hand_landmarks:
            for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                # Get handedness ("Left" or "Right")
                handedness_label = hand_handedness.classification[0].label

                # Count raised fingers
                finger_count = fingers_up(hand_landmarks, handedness_label)

                # Draw hand landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Display handedness and finger count
                x, y = int(hand_landmarks.landmark[0].x * w), int(hand_landmarks.landmark[0].y * h)
                cv2.putText(frame, f"{handedness_label}: {finger_count - 1} fingers", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show the video feed
        cv2.imshow('Hand Detection', frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
