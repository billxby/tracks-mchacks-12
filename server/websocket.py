from websockets.asyncio.server import serve
import cv2
import numpy as np


class WebSocket:
    def __init__(self):
        self.IP = ("localhost", 1235)
        pass

    async def get_frames(self, websocket):
        while True:
            message = await websocket.recv()
            try:
                img_np = np.fromstring(message.decode('base64'), np.uint8)
            except:
                print("Did not receive image from frontend")
                continue;
            frame = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)
            
            yield frame

    async def start_server(self, func):
        print("WebSocket hosting at ws://" + ":".join(self.IP))
        async with serve(func, *self.IP) as server:
            await server.serve_forever()  # Keep running indefinitely
