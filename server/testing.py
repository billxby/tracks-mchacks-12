import asyncio
import websockets
import cv2
import mediapipe as mp
import json
from functools import partial
import spotipy

SPOTIPY_CLIENT_ID = "d64cddc01d3948a293335bd38598056a"
SPOTIPY_CLIENT_SECRET = "828eba458e50416893b17e1f5b0e0954"
SPOTIPY_REDIRECT_URI = "https://example.com/"

scope = ["user-modify-playback-state", "user-read-playback-state"]
sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                              client_secret=SPOTIPY_CLIENT_SECRET,
                                                              redirect_uri=SPOTIPY_REDIRECT_URI,
                                                              scope=scope)) 

device_id = "ade7e71686f3815586d3b61d34772cf14bebd8a4"
track_uri2 = "spotify:track:42VsgItocQwOQC3XWZ8JNA"


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

    async def track_hands(self, websocket, path=None):
        try:
            print("Client connected")
            while True:
                ret, frame = self.video.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)

                hand_data = []
                if results.multi_hand_landmarks:
                    for hand_landmarks, hand_handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        handedness = hand_handedness.classification[0].label
                        fingers = self._count_fingers(hand_landmarks, handedness)
                        
                        if int(fingers) == 2:
                            sp.add_to_queue(track_uri2, device_id)
                            sp.next_track(device_id)

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
                
                await websocket.send(json.dumps(hand_data))
                await asyncio.sleep(0.1)  # 10 FPS
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Client disconnected: {e}")
        finally:
            print("Cleaning up resources")

    async def start_server(self):
        print("WebSocket server starting at ws://localhost:5000")
        async with websockets.serve(self.track_hands, "localhost", 5000):
            await asyncio.Future()  # Keep running indefinitely

if __name__ == "__main__":
    tracker = HandTracker()
    asyncio.run(tracker.start_server())
