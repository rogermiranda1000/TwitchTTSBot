#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import sys
sys.path.append("../audio-server")
from audioserver import AudioServer

from synthesizers.synthesizer import TTSSynthesizer
from pydub import AudioSegment
import shutil

import os
from pathlib import Path
import uuid

import asyncio
import pypeln as pl
from pypeln.utils import Partial,T
from typing import Tuple,List
import multiprocessing as mp

import datetime as dt # bans

class TTSQueue:
    def __init__(self, serve_to: AudioServer, default_synthesizer: TTSSynthesizer, pre_inference: List[Partial[pl.task.Stage[T]]] = None, post_inference: List[Partial[pl.task.Stage[T]]] = None):
        self._serve_to = serve_to
        self._default_synthesizer = default_synthesizer
        
        self._audios_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../audio-server/audios/')

        if pre_inference is None:
            pre_inference = []
        if post_inference is None:
            post_inference = []

        self._current = None
        self._queued_element_notifier = asyncio.Condition()
        self._processing_input = mp.Queue()
        self._play_semaphore = asyncio.Lock() # only one in between `__play` and `__clean`
        self.__init_queue(pre_inference, post_inference)
        self._bans = []

        # website callbacks
        self._website_notifier = asyncio.Condition()
        self._serve_to.on_finish = self.__ended_web_streaming
        self._serve_to.on_timeout = self.__ended_web_streaming

    # @author https://github.com/cgarciae/pypeln/issues/99
    def __init_queue(self, pre_inference: List[Partial[pl.task.Stage[T]]], post_inference: List[Partial[pl.task.Stage[T]]]):
        async def tts_queue():
            while True:
                if self._processing_input.empty():
                    async with self._queued_element_notifier:
                        await self._queued_element_notifier.wait()

                yield self._processing_input.get(block=True, timeout=2)

        queue = pl.task.from_iterable(tts_queue())
        for pre in pre_inference:
            queue = queue | pre
        queue = queue | pl.task.map(self.__infere)
        for post in post_inference:
            queue = queue | post
        queue = queue | pl.task.map(self.__join)                    \
                    | pl.task.map(self.__clean_segments)            \
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
        e = TTSQueueEntry(requested_by, GeneratedTTSSegment(text, self._default_synthesizer))
        self._processing_input.put(e)
        
        # notify the tts_queue loop
        async with self._queued_element_notifier:
            self._queued_element_notifier.notify()

    async def __infere(self, e: TTSQueueEntry) -> TTSQueueEntry:
        """
        Infere TTS
        """
        for index, segment in enumerate(e.segments):
            target_file = str(uuid.uuid4().hex) + '.wav'
            target_path = os.path.join(self._audios_path, target_file)
            print(f"[v] Synthesizing segment {index+1}/{len(e.segments)} into {target_file}...")

            await segment.generate(target_path)

        return e

    async def __join(self, e: TTSQueueEntry) -> TTSQueueEntry:
        target_file = str(uuid.uuid4().hex) + '.wav'
        target_path = os.path.join(self._audios_path, target_file)

        e.path = target_path
        print(f"[v] Joining sub-segments into {e.file_name}...")

        if len(e.segments) == 0:
            return e # invalid

        result = AudioSegment.from_file(e.segments[0].path, format="wav")
        for segment in e.segments[1:]:
            result += AudioSegment.from_file(segment.path, format="wav")
        
        result.export(target_path, format="wav")

        return e

    async def __clean_segments(self, e: TTSQueueEntry) -> TTSQueueEntry:
        for segment in e.segments:
            os.remove(segment.path)

        return e

    async def __play(self, e: TTSQueueEntry) -> TTSQueueEntry:
        """
        Send the TTS path to the website
        """
        await self._play_semaphore.acquire() # only one in between `__play` and `__clean`

        self._bans = [ ban for ban in self._bans if e.requested_on <= ban.until ] # remove expired bans
        e.invalidated = any(e.requested_by == ban.user for ban in self._bans) or e.invalidated or e.processing # if user is banned, or it is invalidated, or it wasn't made at all, then skip
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
        self._bans.append(Ban(requested_by))

        if self._current is not None and self._current.requested_by == requested_by:
            # last request made by the user
            await self._serve_to.interrupt_stream()
            # the file will be removed by the `ended` callback

    async def __ended_web_streaming(self):
        async with self._website_notifier:
            self._website_notifier.notify()

class Ban:
    def __init__(self, user: str, until: dt.datetime = None):
        self._user = user
        self._until = until if until is not None else (dt.datetime.now() + dt.timedelta(seconds=10))

    @property
    def user(self) -> str:
        return self._user

    @property
    def until(self) -> dt.datetime:
        return self._until

class TTSQueueEntry:
    def __init__(self, requested_by: str, *segments: Tuple[TTSSegment, ...], path: str = None, requested_on: dt.datetime = None):
        self._requested_by = requested_by
        self.segments = list(segments)
        self.path = path
        self.invalidated = False
        self._requested_on = requested_on if requested_on is not None else dt.datetime.now()
    
    @property
    def requested_by(self) -> str:
        return self._requested_by

    @property
    def requested_on(self) -> dt.datetime:
        return self._requested_on
    
    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self._path = path

    @property
    def segments(self) -> List[TTSSegment]:
        return self._segments

    @segments.setter
    def segments(self, segments: List[TTSSegment]):
        self._segments = segments
    
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

class TTSSegment:
    def __init__(self):
        self.path = None

    async def generate(self, path: str):
        self.path = path
    
    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self._path = path
    
    @property
    def file_name(self) -> str:
        return None if self._path is None else Path(self._path).name

    @property
    def processing(self) -> bool:
        return self._path is None

class PregeneratedTTSSegment(TTSSegment):
    def __init__(self, copy_from: str):
        super().__init__()
        self._copy_from = copy_from

    async def generate(self, path: str):
        await super().generate(path)
        shutil.copyfile(self._copy_from, path)

class GeneratedTTSSegment(TTSSegment):
    def __init__(self, text: str, synthesizer: TTSSynthesizer):
        super().__init__()
        self._text = text
        self._synthesizer = synthesizer

    async def generate(self, path: str):
        await super().generate(path)
        await self._synthesizer.synthesize(self.text, self.path)
    
    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text

    @property
    def synthesizer(self) -> TTSSynthesizer:
        return self._synthesizer
