#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append("../audio-server")
from webserver import WebServer

import os, json
from bot import TwitchTTSBot
from synthesizers.rvc_synthesizer import RVCTTSSynthesizer

def _get_model_name() -> str:
    config = None
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs/config.json')) as f:
        config = json.load(f)

    return config['model']

def instantiate() -> TwitchTTSBot:
    return TwitchTTSBot.instance(WebServer(), RVCTTSSynthesizer(model=_get_model_name()))