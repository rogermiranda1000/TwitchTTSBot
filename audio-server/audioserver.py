import asyncio
from typing import Callable

class AudioServer:
    def __init__(self, secret_token: str = 'admin', port: int = 7890):
        self._secret_token = secret_token
        self._port = port
        
        self._currently_playing = None
        self.on_finish = lambda: None
        self.on_timeout = lambda: None
    
    async def start(self):
        pass
    
    async def shutdown(self):
        pass

    async def interrupt_stream(self):
        pass
        
    async def stream_audio(self, path: str):
        pass

    @property
    def playing_audio(self) -> bool:
        return self._currently_playing is not None

    @property
    def on_finish(self) -> 'Callable[[],Awaitable[None]]':
        return self._on_finish
    
    @on_finish.setter
    def on_finish(self, on_finish: 'Callable[[],Awaitable[None]]'):
        self._on_finish = on_finish

    @property
    def on_timeout(self) -> 'Callable[[],Awaitable[None]]':
        return self._on_timeout
    
    @on_timeout.setter
    def on_timeout(self, on_timeout: 'Callable[[],Awaitable[None]]'):
        self._on_timeout = on_timeout