#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from buffer import Buffer
from entries import BufferEntry

class SingleBuffer(Buffer):
    def __init__(self, connection: Buffer = None):
        super().__init__(connection)

    @property
    def full(self) -> bool:
        return len(self._list) > 0 # store only 1 element

    @property
    def processing(self) -> bool:
        return self.full

    @property
    def element(self) -> BufferEntry:
        return None if not self.processing else self._list[0]