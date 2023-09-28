#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .synthesizer import TTSSynthesizer

# It will copy an audio file each time `synthesize` is called
class RVCTTSSynthesizer(TTSSynthesizer):
    def synthesize(self, text: str, out: str):
        # TODO temporal
        from .fake_synthesizer import FakeSynthesizer
        FakeSynthesizer('/home/rogermiranda1000/TwitchTTSBot/audio-server/audios/test.wav').synthesize(text,out)

    