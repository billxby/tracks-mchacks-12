import cv2
import mediapipe as mp
import time
import spotipy
import math
import asyncio
import random
import os
import websockets
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Global Variables 
global_songs_list = []

return_values = [
    ['Here are 20 recent or trending songs across the requested BPM ranges, all in the key of C Major:'],
    ["Dua Lipa", "Don't Start Now", "80-120 BPM"],
    ["Ariana Grande", "7 Rings", "120-160 BPM"],
    ["Ed Sheeran", "Shape of You", "100-120 BPM"],
    ["Billie Eilish", "Bad Guy", "110-130 BPM"],
    ["Lizzo", "Good as Hell", "120-140 BPM"],
    ["Vance Joy", "Riptide", "40-60 BPM"],
    ["Lewis Capaldi", "Someone You Loved", "60-80 BPM"],
    ["Lana Del Rey", "Summertime Sadness", "50-70 BPM"],
    ["Maggie Rogers", "Light On", "60-80 BPM"],
    ["Shawn Mendes", "In My Blood", "70-90 BPM"],
    ["The Weeknd", "Blinding Lights", "170-190 BPM"],
    ["Cardi B", "WAP", "160-180 BPM"],
    ["Megan Thee Stallion", "Savage", "155-175 BPM"],
    ["BLACKPINK", "How You Like That", "170-190 BPM"],
    ["BTS", "Dynamite", "175-195 BPM"]
]

# Spotify Utils
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

scopes = ["user-read-playback-state", "user-modify-playback-state", "user-read-private"]
sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                              client_secret=SPOTIPY_CLIENT_SECRET,
                                                              redirect_uri=SPOTIPY_REDIRECT_URI,
                                                              scope=scopes))

def playSong(track_id):
    device_id = "ade7e71686f3815586d3b61d34772cf14bebd8a4"
    sp.add_to_queue(f"spotify:track:{track_id}", device_id)
    sp.next_track(device_id)
    sp.seek_track(random.randint(0, 30)*1000)

def getSongId(track_name, artist):
    searchResult = sp.search(f"track:{track_name} artist:{artist}", type="track")
    return searchResult['tracks']['items'][0]['id']

def processValues(return_values):
    songs_list = []
    for value in return_values:
        if (len(value) < 3):
            continue
        lower, chunk1 = value[2].split('-')
        higher, useless = chunk1.split(' ')
        lower = int(lower)
        higher = int(higher)
        avg_bpm = (lower + higher)//2

        songs_list.append([avg_bpm, value[1], value[0]])
    return sorted(songs_list, key=lambda x: x[0])

def getClosestBPM(target_bpm):
    closest_song = min(global_songs_list, key=lambda x: abs(x[0] - target_bpm))
    return closest_song

def playClosestBPM(target_bpm):
    closest_song = getClosestBPM(target_bpm)
    playSong(getSongId(closest_song[1], closest_song[2]))

FACE_WIDTH = 12
SCREEN_HEIGHT = 1080

class WebSocketClient:
    def __init__(self, uri="ws://10.217.23.251:8765"):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"Connected to WebSocket server at {self.uri}")
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            raise

    async def send_frame(self, frame):
        if not self.websocket:
            await self.connect()
        
        try:
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Send frame
            await self.websocket.send(frame_bytes)
        except Exception as e:
            print(f"Error sending frame: {e}")

    async def receive_frames(self):
        if not self.websocket:
            await self.connect()
        
        try:
            while True:
                frame_bytes = await self.websocket.recv()
                # Convert bytes to numpy array
                np_array = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                yield frame
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Error receiving frame: {e}")

class Chronometer:
    def __init__(self, handchrono):
        self.total_time = 0.0
        self.start_time = 0.0
        self.hc = handchrono
        self.hc.extrema_tracking['elapsed_time'] = 0.0
        self.hc.extrema_tracking['active'] = False

    def start(self):
        if not self.hc.extrema_tracking['active']:
            self.start_time = time.time()
            self.hc.extrema_tracking['active'] = True
            print("Chronometer started at:", self.start_time)

    def stop(self):
        if self.hc.extrema_tracking['active']:
            self.hc.extrema_tracking['elapsed_time'] = time.time() - self.start_time
            self.total_time += self.hc.extrema_tracking['elapsed_time']
            self.hc.extrema_tracking['active'] = False
            print("Chronometer stopped. Elapsed time:", self.hc.extrema_tracking['elapsed_time'])

    def reset(self):
        self.total_time = 0.0
        self.start_time = 0.0
        self.hc.extrema_tracking['elapsed_time'] = 0.0
        self.hc.extrema_tracking['active'] = False
        print("Chronometer reset.")

    @property
    def time(self):
        if self.hc.extrema_tracking['active']:
            return self.total_time + (time.time() - self.start_time)
        return self.total_time

class HandChronometer:
    def __init__(self, websocket_uri="ws://10.217.23.251:8765"):
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, 
            max_num_hands=2, 
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7
        )
        self.last_action_time = 0
        self.action_cooldown = 2.0
        self.exercise_list = ["Curl", "Pushup", "Squat", "Lat Raise"]
        self.this_exercise_index = 0
        self.start_frame = 0
        self.stop_frame = 0

        self.extrema_tracking = {
            'active': False,
            'elapsed_time': 0,
            'max_y': float('-inf'),
            'min_y': float('inf')
        }
        self.chronometer = Chronometer(self)
        self.ws_client = WebSocketClient(websocket_uri)

        #mid-set related variables
        self.bpm_ranges = []
        self.normalAction = False
        self.prev_max_time = 0
        self.BPM_class = None

    def split_into_ranges(self, n):
        step = math.ceil(n / 4)
        return [(i * step + 1, min((i + 1) * step, n)) for i in range(4)]

    def fingers_up(self, hand_landmarks, handedness):
        tips = [4, 8, 12, 16, 20]
        count = 0

        thumb_threshold = 0.02
        finger_threshold = 0.02

        if handedness == "Right":
            if hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 1].x + thumb_threshold:
                count += 1
        else:
            if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x - thumb_threshold:
                count += 1

        for tip in tips[1:]:
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y - finger_threshold:
                count += 1

        return count

    def process_hand_action(self, finger_count, current_time, current_frame):
        if current_time - self.last_action_time < self.action_cooldown:
            return

        FRAME_BUFFER = 20

        if finger_count == 2:  # Two fingers up
            #if set not started 
            if not self.extrema_tracking['active'] and current_frame >= self.stop_frame + FRAME_BUFFER:
                print("Two fingers detected. Activating.")
                self.chronometer.start()
                self.extrema_tracking['max_y'] = float('-inf')
                self.extrema_tracking['min_y'] = float('inf')
                self.last_action_time = current_time
                self.start_frame = current_frame
                self.normalAction = False
            #if set has already started
            elif self.chronometer.time >= 4 and current_frame >= self.start_frame + FRAME_BUFFER:
                self.chronometer.stop()
                print(f"Exercise {self.exercise_list[self.this_exercise_index]} Extrema:")
                print(f"Max Y: {self.extrema_tracking['max_y']}")
                print(f"Min Y: {self.extrema_tracking['min_y']}")
                self.extrema_tracking['max_y'] = float('-inf')
                self.extrema_tracking['min_y'] = float('inf')
                self.last_action_time = current_time
        elif finger_count == 3:  # Three fingers up
            self.bpm_ranges = []
            self.normalAction = False
            self.prev_max_time = 0
            self.chronometer.reset()
            self.this_exercise_index = (self.this_exercise_index + 1) % len(self.exercise_list)
            self.last_action_time = current_time

    async def run(self):
        try:
            await self.ws_client.connect()
            
            current_frame = 0
            
            async for frame in self.ws_client.receive_frames():
                current_frame += 1
                this_exercise = self.exercise_list[self.this_exercise_index]

                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                current_time = time.time()

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hand_result = self.hands.process(rgb_frame)
                pose_result = self.pose.process(rgb_frame)

                pose_landmarks = pose_result.pose_landmarks
                
                time_text = f"Time: {self.chronometer.time:.2f} sec"
                cv2.putText(frame, time_text, (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                exercise_text = f"Exercise: {self.exercise_list[self.this_exercise_index]}"
                cv2.putText(frame, exercise_text, (10, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if pose_landmarks and self.extrema_tracking['active']:
                    self.mp_drawing.draw_landmarks(frame, pose_result.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                    right_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EAR.value]
                    left_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EAR.value]

                    right_ear_x, right_ear_y = right_ear.x * new_width, right_ear.y * new_height
                    left_ear_x, left_ear_y = left_ear.x * new_width, left_ear.y * new_height
                    propConstant = FACE_WIDTH / (((right_ear_y - left_ear_y) ** 2 + (right_ear_x - left_ear_x) ** 2) ** 0.5)

                    if this_exercise == "Squat" or this_exercise == "Pushup":
                        right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                        left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]

                        right_y = right_shoulder.y * new_height * propConstant
                        left_y = left_shoulder.y * new_height * propConstant
                    else:
                        right_wrist = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
                        left_wrist= pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST.value]

                        right_y = right_wrist.y * new_height * propConstant
                        left_y = left_wrist.y * new_height * propConstant
                    
                    avg_y = (right_y + left_y) / 2
                    self.extrema_tracking['max_y'] = max(self.extrema_tracking['max_y'], avg_y)
                    self.extrema_tracking['min_y'] = min(self.extrema_tracking['min_y'], avg_y)
                    
                    
                    if current_time - self.chronometer.start_time > 4:
                        localMax, localMin = self.extrema_tracking["max_y"], self.extrema_tracking["min_y"]
                        
                        if not self.bpm_ranges:
                            self.bpm_ranges = self.split_into_ranges(80)
                        
                        diff = 1/propConstant
                        REP_BUFFER = 0.7
                        if this_exercise == "Pushup":
                            REP_BUFFER = 1.5
                        elif this_exercise == "Curl":
                            REP_BUFFER = 0.7
                        elif this_exercise == "Lat Raise":
                            REP_BUFFER = 1
                        elif this_exercise == "Squat":
                            REP_BUFFER = 1.5
                        if localMin - diff <= avg_y <= localMin + diff and current_time - self.prev_max_time > REP_BUFFER:
                            bpm = 1 / ((current_time - self.prev_max_time)/60)
                            for i, bounds in enumerate(self.bpm_ranges):
                                startBPM, endBPM = bounds
                                if startBPM < bpm < endBPM:
                                    if i != self.BPM_class:
                                        self.BPM_class = i
                                        print("Previous class :" + str(self.BPM_class) + '; ' + "This class: " + str(i))
                                        playClosestBPM(bpm * 2.5)

                                
                            print(str(bpm) + ' reps per minute')
                            self.prev_max_time = current_time

                if pose_landmarks and hand_result.multi_hand_landmarks:
                    right_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_EAR.value]
                    left_ear = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_EAR.value]

                    right_ear_x, right_ear_y = right_ear.x * new_width, right_ear.y * new_height
                    left_ear_x, left_ear_y = left_ear.x * new_width, left_ear.y * new_height
                    propConstant = FACE_WIDTH / (((right_ear_y - left_ear_y) ** 2 + (right_ear_x - left_ear_x) ** 2) ** 0.5)
                    
                    left_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP.value]
                    right_hip = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
                    
                    left_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                    right_shoulder = pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                    
                    avg_threshold_y = ((left_hip.y + left_shoulder.y)/2 + (right_hip.y + right_shoulder.y)/2)/2 * new_height * propConstant 
                    for hand_landmarks, hand_handedness in zip(hand_result.multi_hand_landmarks, hand_result.multi_handedness):
                        wrist_y = hand_landmarks.landmark[0].y * new_height * propConstant
                        if avg_threshold_y < wrist_y:
                            continue
                        
                        handedness_label = hand_handedness.classification[0].label
                        finger_count = self.fingers_up(hand_landmarks, handedness_label)

                        self.process_hand_action(finger_count, current_time, current_frame)

                        self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                        x, y = int(hand_landmarks.landmark[0].x * w), int(hand_landmarks.landmark[0].y * h)
                        cv2.putText(frame, f"{handedness_label}: {finger_count} fingers", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow('Hand Chronometer', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                await self.ws_client.send_frame(frame)

        except Exception as e:
            print(f"HandChronometer run error: {e}")

class WebSocketServer:
    def __init__(self, host='10.217.23.251', port=8765):
        self.host = host
        self.port = port

    async def handle_client(self, websocket, path=None):
        try:
            async for message in websocket:
                print(f"Received message: {message}")
                await websocket.send("Frame received")
        except Exception as e:
            print(f"WebSocket server error: {e}")

    async def start_server(self):
        server = await websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            max_size = None
        )
        print(f"WebSocket server started on {self.host}:{self.port}")
        await server.wait_closed()

async def main():
    global global_songs_list
    global_songs_list = processValues(return_values)

    # Option 1: Start server
    server = WebSocketServer()
    server_task = asyncio.create_task(server.start_server())

    # Option 2: Run HandChronometer
    hand_chrono = HandChronometer()
    await hand_chrono.run()

    await server_task

if __name__ == "__main__":
    asyncio.run(main())