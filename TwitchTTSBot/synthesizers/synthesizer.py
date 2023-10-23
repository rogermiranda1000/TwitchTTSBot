#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

class TTSSynthesizer:
    def __init__(self, name: str):
        self._model_name = name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def synthesize(self, text: str, out: str):
        pass