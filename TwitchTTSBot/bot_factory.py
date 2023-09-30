#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append("../audio-server")
from webserver import WebServer

import os, json
from bot import TwitchTTSBot
from synthesizers.rvc_synthesizer import RVCTTSSynthesizer
from functools import cache

import pypeln as pl
import asyncio
from tts_queue import TTSQueueEntry

@cache
def _get_config_json() -> json:
    config = None
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs/config.json')) as f:
        config = json.load(f)
    return config

def _get_model_name() -> str:
    return _get_config_json()['model']

def _get_character_limit() -> int:
    return None if 'input_limit' not in _get_config_json() else _get_config_json()['input_limit']

def instantiate() -> TwitchTTSBot:
    queue_pre_inference = []
    queue_post_inference = []

    # character limit
    character_limit = _get_character_limit()
    if character_limit is not None:
        async def truncate_input(e: TTSQueueEntry):
            e.segments[0].text = e.segments[0].text[:character_limit]
            return e

        queue_pre_inference.append(pl.task.map(truncate_input))

    # return the instance
    return TwitchTTSBot.instance(WebServer(), RVCTTSSynthesizer(model=_get_model_name()), queue_pre_inference=queue_pre_inference, queue_post_inference=queue_post_inference)