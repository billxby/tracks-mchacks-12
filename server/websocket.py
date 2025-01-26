from websockets.asyncio.server import serve
import cv2
import numpy as np


class WebSocket:
    def __init__(self):
        self.IP = ("localhost", "1235")
        self.ws = None
        pass

    async def get_frames(self):
        if not self.ws:
            print("WebSocket not initiated")
            return

        while True:
            message = await self.ws.recv()
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
        print("WebSocket hosting at ws://" + ":".join(self.IP))
        async with serve(self.set_ws, *self.IP) as server:
            await server.serve_forever()  # Keep running indefinitely
