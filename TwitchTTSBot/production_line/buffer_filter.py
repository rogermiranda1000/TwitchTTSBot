#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from buffer import Buffer
from entries import BufferEntry
from null_buffer import NullBuffer
from typing import Callable

class BufferObserver(NullBuffer):
    """
    Object to be placed in between a production line to raise a callback each element
    it goes through.
    """
    def __init__(self, filter: Callable[[BufferEntry],bool], connection: Buffer = None):
        super().__init__(connection)
        self._filter = filter
        
    def enqueue(self, e: BufferEntry):
        if self.filter(e):
            super().enqueue(e)
        # else, discard