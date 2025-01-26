import asyncio
from websockets.asyncio.server import serve
import cv2
import mediapipe as mp
import numpy as np
import json
from functools import partial
import spotipy

IP = ("localhost", 1235)


class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=2, 
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )
        self.video = cv2.VideoCapture(0)

    def _count_fingers(self, hand_landmarks, handedness):
        tips = [4, 8, 12, 16, 20]
        count = 0
        
        # Thumb logic
        if handedness == "Right":
            if hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 1].x:
                count += 1
        else:
            if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x:
                count += 1
        
        # Other fingers
        for tip in tips[1:]:
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
                count += 1
        
        return count - 1

    async def track_hands(self, websocket):
        while True:
            message = await websocket.recv()
            try:
                img_np = np.fromstring(message.decode('base64'), np.uint8)
            except:
                print("Did not receive image from frontend")
                continue;
            frame = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)

            # ret, frame = self.video.read()
            # if not ret:
            #     break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            hand_data = []
            if results.multi_hand_landmarks:
                for hand_landmarks, hand_handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    handedness = hand_handedness.classification[0].label
                    fingers = self._count_fingers(hand_landmarks, handedness)

                    hand_info = {
                        'handedness': handedness,
                        'fingers': fingers,
                        'landmarks': [
                            {'x': lm.x, 'y': lm.y, 'z': lm.z}
                            for lm in hand_landmarks.landmark
                        ]
                    }
                    hand_data.append(hand_info)
            print(f"Detected {len(hand_data)} hands")


    async def start_server(self):
        print("WebSocket hosting at ws://" + ":".join(IP))
        async with serve(self.track_hands, *IP) as server:
            await server.serve_forever()  # Keep running indefinitely

if __name__ == "__main__":
    tracker = HandTracker()
    asyncio.run(tracker.start_server())
