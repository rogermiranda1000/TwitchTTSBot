from audioserver import AudioServer
from aiohttp import web
import socketio
import ssl
import re
import os
import asyncio
from pathlib import Path
from pydub import AudioSegment

class WebServer(AudioServer):
    def __init__(self, secret_token: str = 'admin', port: int = 7890):
        super().__init__(secret_token, port)
        self._base_path = os.path.dirname(os.path.abspath(__file__))
        self._audios_path = os.path.join(self._base_path, './audios/')
        self._currently_playing_timeout_task = None

    async def start(self):
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
                
            with open(os.path.join(self._base_path, 'index.html')) as f:
                return web.Response(text=f.read(), content_type='text/html')
        
        async def resource(request):
            if not 'token' in request.rel_url.query or request.rel_url.query['token'] != self._secret_token:
                raise web.HTTPUnauthorized()

            path = re.sub(r'[^a-zA-Z0-9\.]', '', request.match_info['audio'])
            full_path = os.path.join(self._audios_path, path)
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
        ssl_context.load_cert_chain(os.path.join(self._base_path, 'server.pem'), os.path.join(self._base_path, 'key.pem'))

        # We kick off our server
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, port=self._port, ssl_context=ssl_context)    
        await self._site.start()
    
    async def shutdown(self):
        pass # TODO
    
    async def interrupt_stream(self):
        if self.playing_audio:
            # one audio is playing; stop it
            self._currently_playing = None
            await self._sio.emit('interrupt', '')
            await self.on_finish()
    
    # @pre No audio should be playing
    # @pre The file should be in the website's "resources" path
    async def stream_audio(self, path: str):
        #if self.playing_audio:
        #    return

        target_file = Path(path).name
        self._currently_playing = target_file
        print(f"[v] Serving {target_file}...")
        await self._sio.emit('audio', target_file)

        audio = AudioSegment.from_wav(path)
        timeout_wait = max(audio.duration_seconds * 1.5, 5) # wait 5s, or 1.5 times the audio length
        print(f"[v] Play timeout set to {timeout_wait}s")
        async def timeout_task():
            await asyncio.sleep(timeout_wait)
            await self._stream_timedout(target_file)
        self._currently_playing_timeout_task = asyncio.create_task(timeout_task())
    
    async def _stream_ended(self, file: str):
        print(f"[v] Finished streaming audio '{file}'")

        # stop the timeout task
        if self._currently_playing_timeout_task is not None:
            self._currently_playing_timeout_task.cancel()

        if file == self._currently_playing:
            self._currently_playing = None
            await self.on_finish()
    
    async def _stream_timedout(self, file: str):
        print(f"[v] Timeout on audio '{file}'")

        if file == self._currently_playing:
            self._currently_playing = None
            await self.on_timeout()

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