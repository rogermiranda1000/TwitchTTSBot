#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any

class BufferEntry:
    def __init__(self):
        pass

class PrimitiveBufferEntry(BufferEntry):
    def __init__(self, element: Any):
        self._element = element
    
    @property
    def element(self):
        return self._element