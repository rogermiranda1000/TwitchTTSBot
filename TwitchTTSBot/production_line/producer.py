#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from buffer import Buffer
from entries import BufferEntry
from single_buffer import SingleBuffer
from typing import List

class Producer(SingleBuffer):
    """
    An abstract class that converts elements from a Buffer list into different elements.
    As only one element (a SingleBuffer) is being processed at a time, it will need to tell the previous buffer when it needs a new one.
    If connected to a buffer, it will enqueue all produced elements, otherwise they will be lost.
    """
    def __init__(self, connection: Buffer = None):
        super().__init__(connection)

    async def process(self, e: BufferEntry):
        """
        An element can be processed.
        Once is processed, you should call `_done_processing` with the result of the processing.

        :param e: Element to forward to the buffer
        """
        pass

    async def interrupt(self):
        """
        The element being processed cannot be forwarded.
        """
        pass

    async def _done_processing(self, result: BufferEntry):
        if self.connection is not None and not self.connection.full:
            await self.connection.enqueue(result) # forward the result to the next buffer
        self._list.clear() # remove processed element
        await self.forward_petition() # request a new element
        
    async def enqueue(self, e: BufferEntry):
        super().enqueue(e)
        self.process(e)

    async def __elements_were_removed(self, elements: List[BufferEntry]):
        await self.interrupt()