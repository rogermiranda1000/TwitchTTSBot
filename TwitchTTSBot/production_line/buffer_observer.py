#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from buffer import Buffer
from entries import BufferEntry
from null_buffer import NullBuffer
from collections.abc import Callable, Awaitable

class BufferObserver(NullBuffer):
    """
    Object to be placed in between a production line to raise a callback each element
    it goes through.
    """
    def __init__(self, callback: Callable[[BufferEntry],Awaitable[None]], connection: Buffer = None):
        super().__init__(connection)
        self._callback = callback
        
    def enqueue(self, e: BufferEntry):
        Buffer._get_event_loop().run_until_complete(self._callback(e))
        super().enqueue(e)