from websockets.asyncio.server import serve
import cv2
import numpy as np
import asyncio


class WebSocket:
    def __init__(self):
        self.IP = ("localhost", "1235")
        self.ws = None

    def get_frames(self):
        while True:
            message = asyncio.run(self.ws.recv())
            try:
                img_np = np.fromstring(message.decode('base64'), np.uint8)
            except:
                print("Did not receive image from frontend")
                continue;
            frame = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)
            
            yield frame
            
    def set_ws(self, websocket):
        self.ws = websocket

    async def start_server(self):
        def set_ws(websocket):
            nonlocal self
            self.ws = websocket
        async with serve(set_ws, *self.IP) as server:
            print("WebSocket hosting at ws://" + ":".join(self.IP))
            await server.serve_forever()  # Keep running indefinitely
