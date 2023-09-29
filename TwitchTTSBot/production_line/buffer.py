#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import asyncio
from collections.abc import Callable, Awaitable
from entries import BufferEntry

class Buffer:
    """
    A class that consumes elements.
    Any previous producer will just add element to this (infinite) list.
    """
    def __init__(self, connection: Buffer = None):
        self._list = []
        self.connection = connection
        self.forward_petition = lambda: None # connected to nothing
    
    async def enqueue(self, e: BufferEntry):
        if self.full:
            raise Exception("Can't enqueue element: list is already full")

        self._list.append(e)
        await self.__forward() # it will fail if it can't forward it

    async def __forward(self):
        if len(self._list) == 0 or self.connection is None or self.connection.full:
            return # nothing to enqueue, or nowhere to forward, or forward is busy

        await self.connection.enqueue(self._list.pop(0))

    async def _forward_request(self):
        """
        The connection requests to get an element
        """
        await self.__forward() # it will fail if it can't forward it

    async def erase(self, should_remove: Callable[[BufferEntry],bool]):
        to_remove = list(filter(should_remove, self._list))
        if len(to_remove) > 0:
            self._list = [e for e in self._list if e not in to_remove]
            await self.__elements_were_removed(to_remove)
            if not self.full():
                await self.forward_petition() # we've removed elements; fill the slots (if the previous connection can)
        await self.connection.erase(should_remove)

    async def __elements_were_removed(self, elements: List[BufferEntry]):
        pass

    async def erase_all(self):
        await self.erase(lambda e: True)

    @property
    def full(self) -> bool:
        return False
    
    @property
    def connection(self) -> Buffer:
        return self._connection

    @connection.setter
    def connection(self, connection: Buffer):
        self._connection = connection
        if self._connection is not None:
            self._connection.forward_petition = self._forward_request
    
    @property
    def forward_petition(self) -> Callable[[], Awaitable[None]]:
        return self._forward_petition

    @forward_petition.setter
    def forward_petition(self, forward_petition: Callable[[], Awaitable[None]]):
        self._forward_petition = forward_petition
