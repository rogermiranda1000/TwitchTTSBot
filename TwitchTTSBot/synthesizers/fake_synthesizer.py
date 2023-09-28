#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
from synthesizer import TTSSynthesizer

# It will copy an audio file each time `synthesize` is called
class FakeSynthesizer(TTSSynthesizer):
    def __init__(self, copy_from: str):
        self._copy_from = copy_from

    def synthesize(self, text: str, out: str):
        shutil.copyfile(self._copy_from, out)

    