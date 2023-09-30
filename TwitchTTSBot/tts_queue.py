#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import sys
sys.path.append("../audio-server")
from audioserver import AudioServer

from synthesizers.synthesizer import TTSSynthesizer

import os
from pathlib import Path
import uuid

import asyncio
import pypeln as pl
from pypeln.utils import A
from typing import Union
import multiprocessing as mp

class TTSQueue:
    def __init__(self, serve_to: AudioServer, synthesizer: TTSSynthesizer, pre_inference: Union[Stage[A], pypeln_utils.Partial[Stage[A]]] = pl.task.filter(lambda e: True), post_inference: Union[Stage[A], pypeln_utils.Partial[Stage[A]]] = pl.task.filter(lambda e: True)):
        self._serve_to = serve_to
        self._synthesizer = synthesizer
        
        self._audios_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../audio-server/audios/')

        self._current = None
        self._queued_element_notifier = asyncio.Condition()
        self._processing_input = mp.Queue()
        self._play_semaphore = asyncio.Lock() # only one in between `__play` and `__clean`
        self.__init_queue(pre_inference, post_inference)
        self._bans = set()

        # website callbacks
        self._website_notifier = asyncio.Condition()
        self._serve_to.on_finish = self.__ended_web_streaming
        self._serve_to.on_timeout = self.__ended_web_streaming

    # @author https://github.com/cgarciae/pypeln/issues/99
    def __init_queue(self, pre_inference: Union[Stage[A], pypeln_utils.Partial[Stage[A]]], post_inference: Union[Stage[A], pypeln_utils.Partial[Stage[A]]]):
        async def tts_queue():
            while True:
                if self._processing_input.empty():
                    async with self._queued_element_notifier:
                        await self._queued_element_notifier.wait()

                yield self._processing_input.get(block=True, timeout=2)

        queue = pl.task.from_iterable(tts_queue())                  \
                    | pre_inference                                 \
                    | pl.task.map(self.__infere)                    \
                    | post_inference                                \
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
        e = TTSQueueEntry(requested_by, text, target_path)
        self._processing_input.put(e)
        
        # notify the tts_queue loop
        async with self._queued_element_notifier:
            self._queued_element_notifier.notify()

    async def __infere(self, e: TTSQueueEntry) -> TTSQueueEntry:
        """
        Infere TTS
        """
        print(f"[v] Synthesizing '{e.text}' into {e.file_name}")

        target_path = e.path # the target_path is the path set by the last iterator
        await self._synthesizer.synthesize(e.text, target_path)

        print(f"[v] '{e.text}' synthetized.")
        return e

    async def __play(self, e: TTSQueueEntry) -> TTSQueueEntry:
        """
        Send the TTS path to the website
        """
        await self._play_semaphore.acquire() # only one in between `__play` and `__clean`

        e.invalidated = e.requested_by in self._bans
        if not e.invalidated:
            await self._serve_to.stream_audio(e.path)
            self._current = e
        return e

    async def __wait_for_streaming(self, e: TTSQueueEntry):
        if not e.invalidated:
            async with self._website_notifier:
                await self._website_notifier.wait() # wait for the website to call `__ended_web_streaming`
        return e

    async def __clean(self, e: TTSQueueEntry):
        self._current = None
        self._play_semaphore.release()

        print(f"[v] Cleaning {e.file_name}...")
        os.remove(e.path) # remove (already played) file

        return None # finished

    async def erase(self, requested_by: str):
        self._bans.add(requested_by)

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
        self.invalidated = False
    
    @property
    def requested_by(self) -> str:
        return self._requested_by
    
    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text
    
    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self._path = path
    
    @property
    def invalidated(self) -> bool:
        return self._invalidated

    @invalidated.setter
    def invalidated(self, invalidated: bool):
        self._invalidated = invalidated
    
    @property
    def file_name(self) -> str:
        return None if self._path is None else Path(self._path).name

    @property
    def processing(self) -> bool:
        return self._path is None