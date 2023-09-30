#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import sys
sys.path.append("../audio-server")
from audioserver import AudioServer

from synthesizers.synthesizer import TTSSynthesizer

import os
import uuid

import asyncio
import pypeln as pl
import multiprocessing as mp

class TTSQueue:
    def __init__(self, serve_to: AudioServer, synthesizer: TTSSynthesizer):
        self._serve_to = serve_to
        self._synthesizer = synthesizer
        
        self._audios_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../audio-server/audios/')

        self._current = None
        self._queued_element_notifier = asyncio.Condition()
        self._processing_input = mp.Queue()
        self.__init_queue()

        # website callbacks
        self._website_notifier = asyncio.Condition()
        self._serve_to.on_finish = self.__ended_web_streaming
        self._serve_to.on_timeout = self.__ended_web_streaming

    # @author https://github.com/cgarciae/pypeln/issues/99
    def __init_queue(self):
        async def tts_queue():
            while True:
                async with self._queued_element_notifier:
                    await self._queued_element_notifier.wait()
                item = self._processing_input.get(block=True, timeout=2)

                if item is not None:
                    yield item

        queue = pl.task.from_iterable(tts_queue())                  \
                    | pl.task.map(self.__infere)                    \
                    | pl.task.filter(self.__is_filtered)            \
                    | pl.task.map(self.__play)                      \
                    | pl.task.map(self.__wait_for_streaming)        \
                    | pl.task.map(self.__clean)                     \

        async def start_queue():
            while True:
                # just iterate
                async for _ in queue.__aiter__():
                    pass

        asyncio.get_event_loop().create_task(start_queue())
        # TODO stop thread when closing

    async def enqueue(self, requested_by: str, text: str):
        target_file = str(uuid.uuid4().hex) + '.wav'
        target_path = os.path.join(self._audios_path, target_file)
        print(f"[v] Synthesizing '{text}' into {target_file}")
        e = TTSQueueEntry(requested_by, text, target_path)
        self._processing_input.put(e)
        
        # notify the tts_queue loop
        async with self._queued_element_notifier:
            self._queued_element_notifier.notify()

    async def __infere(self, e: TTSQueueEntry) -> TTSQueueEntry:
        """
        Infere TTS
        """
        target_path = e.path # the target_path is the path set by the last iterator
        self._synthesizer.synthesize(e.text, target_path)
        return e

    async def __is_filtered(self, e: TTSQueueEntry) -> bool:
        return True # TODO add a filter list

    async def __play(self, e: TTSQueueEntry) -> TTSQueueEntry:
        """
        Send the TTS path to the website
        """
        # TODO what if the filter is already done and `erase` gets called before `__play`?
        await self._serve_to.stream_audio(e.path)
        self._current = e
        return e

    async def __wait_for_streaming(self, e: TTSQueueEntry):
        async with self._website_notifier:
            await self._website_notifier.wait() # wait for the website to call `__ended_web_streaming`
        return e

    async def __clean(self, e: TTSQueueEntry):
        os.remove(e.path) # remove (already played) file
        self._current = None
        return None # finished

    async def erase(self, requested_by: str):
        # TODO add a filter for tasks before playing

        if self._current is not None and self._current.requested_by == requested_by:
            # last request made by the user
            await self._serve_to.interrupt_stream()
            # the file will be removed by the `ended` callback

    async def __ended_web_streaming(self):
        async with self._website_notifier:
            self._website_notifier.notify()

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

    @property
    def processing(self) -> bool:
        return self._path is None