from __future__ import annotations
from aiohttp import web
import socketio
import ssl

import re
import os

import uuid
import shutil

from threading import Thread,Lock

import asyncio
from time import sleep

class WebServer:
    def __init__(self, secret_token: str = 'admin', port: int = 7890):
        self._base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './audios/')
        self._secret_token = secret_token
        self._port = port

        self._queue_lock = Lock()
        self._currently_playing = None
        self._play_queue = []

    async def start(self) -> WebServer:
        # creates a new Async Socket IO Server
        self._sio = socketio.AsyncServer(async_mode='aiohttp', logger=True, engineio_logger=True, cors_allowed_origins='*')
        # Creates a new Aiohttp Web Application
        self._app = web.Application()
        # Binds our Socket.IO server to our Web App instance
        self._sio.attach(self._app)
        
        ## If we wanted to create a new websocket endpoint,
        ## use this decorator, passing in the name of the
        ## event we wish to listen out for
        @self._sio.on('message')
        async def listen_for_ended(sid, message):
            #print("Socket ID: " , sid)
            #print(message)

            if not isinstance(message, dict) or not 'token' in message or message['token'] != self._secret_token:
                return # invalid
            
            if not 'audio' in message or len(message['audio']) == 0:
                return # invalid

            await self._stream_ended(re.search(r"([A-Za-z0-9]+\.wav)", message['audio']).group(1))
        
        ## we can define aiohttp endpoints just as we normally
        ## would with no change
        async def index(request):
            if not 'token' in request.rel_url.query or request.rel_url.query['token'] != self._secret_token:
                raise web.HTTPUnauthorized()
                
            with open('index.html') as f:
                return web.Response(text=f.read(), content_type='text/html')
        
        async def resource(request):
            if not 'token' in request.rel_url.query or request.rel_url.query['token'] != self._secret_token:
                raise web.HTTPUnauthorized()

            path = re.sub(r'[^a-zA-Z0-9\.]', '', request.match_info['audio'])
            full_path = os.path.join(self._base_path, path)
            #print(full_path)
            
            try:
                with open(full_path, 'rb') as f:
                    return web.Response(body=f.read(), content_type='audio/wav')
            except Exception as e:
                print(str(e))
                raise web.HTTPNotFound()

        # We bind our aiohttp endpoint to our app router
        self._app.router.add_get('/', index)
        # Audios
        self._app.router.add_get('/audios/{audio}', resource)

        # https
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain('server.pem', 'key.pem')

        # We kick off our server
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, port=self._port, ssl_context=ssl_context)    
        await self._site.start()
    
    async def interrupt_stream(self):
        with self._queue_lock: # don't play between interrupting!
            await self._sio.emit('interrupt', '')
            await self._done_playing()
    
    async def stream_audio(self, path: str):
        target_file = str(uuid.uuid4().hex) + '.wav'
        target_path = os.path.join(self._base_path, target_file)
        shutil.copyfile(path, target_path)
        
        with self._queue_lock:
            self._play_queue.append(target_file)
        await self.__stream_audio()

    async def __stream_audio(self):
        target_file = None
        with self._queue_lock:
            if self.playing_audio or not self.are_queued_elements:
                return # we'll play it once it finishes (or nothing to play)

            target_file = self._play_queue.pop(0)
            self._currently_playing = target_file
        print(f"[v] Serving {target_file}...")
        await self._sio.emit('audio', target_file)
    
    async def _stream_ended(self, file: str):
        print(f"[v] Finished streaming audio '{file}'")

        with self._queue_lock:
            if file == self._currently_playing:
                await self._done_playing()
    
    async def _stream_timedout(self, file: str):
        print(f"[v] Timeout on audio '{file}'")

        with self._queue_lock:
            if file == self._currently_playing:
                await self._done_playing()
    
    async def _done_playing(self):
        # always called from a safe environment
        #with self._queue_lock:
            # remove audio
            if self._currently_playing is not None:
                absolute_path = os.path.join(self._base_path, self._currently_playing)
                os.remove(absolute_path)

            self._currently_playing = None
            if self.are_queued_elements:
                await self.__stream_audio()

    @property
    def playing_audio(self) -> bool:
        return self._currently_playing is not None

    @property
    def are_queued_elements(self) -> bool:
        return len(self._play_queue) > 0

if __name__ == '__main__':
    website = WebServer()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(website.start())

    async def play_sound():
        await asyncio.sleep(8)
        print("[v] Playing sound")
        await website.stream_audio('./audios/test.wav')

    loop.run_until_complete(play_sound())
    loop.run_forever()