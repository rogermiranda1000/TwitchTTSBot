#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from buffer import Buffer
from entries import BufferEntry

class NullBuffer(Buffer):
    """
    A buffer that only observes processing objects; it cannot hold any object inside it,
    so it will just forward it.
    """
    def __init__(self, connection: Buffer = None):
        super().__init__(connection)

    @property
    def full(self) -> bool:
        return False if self.connection is None else self.connection.full