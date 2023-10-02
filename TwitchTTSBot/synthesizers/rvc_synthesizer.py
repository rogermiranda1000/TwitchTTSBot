#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import asyncio
from .synthesizer import TTSSynthesizer

class RVCModel:
    def __init__(self, alias: str, model_name: str, model_voice: str):
        self._alias = alias
        self._model_name = model_name
        self._model_voice = model_voice

    @property
    def alias(self) -> str:
        return self._alias

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_voice(self) -> str:
        return self._model_voice

# It will copy an audio file each time `synthesize` is called
class RVCTTSSynthesizer(TTSSynthesizer):
    def __init__(self, model: RVCModel):
        self._model = model

    @property
    def model(self) -> RVCModel:
        return self._model

    async def synthesize(self, text: str, out: str):
        # calling `infere` directly won't work for permissions issue (needs to be sudo)
        python_full_path = sys.executable
        infere_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../rvc-tts-webui/infere.py')
        proc = await asyncio.create_subprocess_exec('sudo',python_full_path,infere_path, '--model', self._model.model_name, '--text', text, '--out', out, '--voice', self._model.model_voice,
                                                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()