#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append("../audio-server")
from audioserver import AudioServer

from synthesizers.synthesizer import TTSSynthesizer

import os
import uuid

class TTSQueue:
    def __init__(self, serve_to: AudioServer, synthesizer: TTSSynthesizer):
        self._serve_to = serve_to
        self._synthesizer = synthesizer
        
        self._audios_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './audios/')

        self._queue = []
        self._current = None

        self._serve_to.on_finish = self.__ended
        self._serve_to.on_timeout = self.__ended

    async def enqueue(self, requested_by: str, text: str):
        target_file = str(uuid.uuid4().hex) + '.wav'
        target_path = os.path.join(self._audios_path, target_file)
        print(f"[v] Synthesizing '{text}' into {target_file}")

        # infere TTS & append to list
        self._synthesizer.synthesize(text, target_path)
        self._queue.append(TTSQueueEntry(requested_by, text, target_path))

        if not self._serve_to.playing_audio:
            await self.__forward()

    async def __forward(self):
        if len(self._queue) == 0:
            return # nothing to play

        self._current = self._queue.pop(0)
        await self._serve_to.stream_audio(self._current.path)

    async def __ended(self):
        # ended playing the last audio
        self._current = None

        # can we play a next one?
        if len(self._queue) > 0:
            await self.__forward()

    async def erase(self, requested_by: str):
        self._queue = [r for r in self._queue if r.requested_by != requested_by]
        if self._current is not None and self._current.requested_by == requested_by:
            # last request made by the user
            await self._serve_to.interrupt_stream()

class TTSQueueEntry:
    def __init__(self, requested_by: str, text: str, path: str = None):
        self._requested_by = requested_by
        self._text = text
        self.path = path
    
    @property
    def requested_by(self) -> str:
        return self._requested_by
    
    @property
    def text(self) -> str:
        return self._text
    
    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self._path = path