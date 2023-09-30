#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import asyncio
from .synthesizer import TTSSynthesizer

# It will copy an audio file each time `synthesize` is called
class RVCTTSSynthesizer(TTSSynthesizer):
    def __init__(self, model: str):
        self._model = model

    async def synthesize(self, text: str, out: str):
        # calling `infere` directly won't work for permissions issue (needs to be sudo)
        python_full_path = sys.executable
        infere_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../rvc-tts-webui/infere.py')
        proc = await asyncio.create_subprocess_exec('sudo',python_full_path,infere_path, '--model', self._model, '--text', text, '--out', out)
        tdout, stderr = await proc.communicate()

    