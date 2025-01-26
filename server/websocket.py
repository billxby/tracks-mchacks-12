# from websockets.asyncio.server import serve
# import cv2
# import numpy as np
# import asyncio
# import time
# import websockets

# class WebSocket:
#     def __init__(self):
#         self.IP = ("localhost", 59548)
#         self.ws = None

#     async def get_frames(self):
#         while True:
#             if self.ws is None:
#                 asyncio.sleep(0.1)  # Wait for the WebSocket connection
#                 continue

#             try:
#                 message = await self.ws.recv()  # Use await to receive messages asynchronously
#                 print("got msg", message)
#                 img_np = np.frombuffer(message.encode('utf-8'), np.uint8)  # Adjusted decoding method
#             except Exception as e:
#                 print(f"Error while receiving frame: {e}")
#                 continue
#             frame = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)
#             yield frame


#     async def start_server(self):
#         async def set_ws(websocket):
#             self.ws = websocket
#             print("WebSocket connection established.")
#         print("Starting WebSocket server...")
#         async with websockets.serve(set_ws, *self.IP) as server:
#             print("WebSocket hosting at ws://" + ":".join(map(str, self.IP)))
#             await asyncio.Future()  # Keeps the server running indefinitely

