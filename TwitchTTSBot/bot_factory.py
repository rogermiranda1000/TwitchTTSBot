#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append("../audio-server")
from webserver import WebServer

import os, json, uuid, random, re
from typing import List
from bot import TwitchTTSBot
from synthesizers.synthesizer import TTSSynthesizer
from synthesizers.rvc_synthesizer import RVCTTSSynthesizer,RVCModel
from functools import cache

import pypeln as pl
import asyncio
from tts_queue import TTSQueueEntry, TTSSegment, GeneratedTTSSegment, PregeneratedTTSSegment

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

def _get_segments_limit() -> int:
    return None if 'segments_limit' not in _get_config_json() else _get_config_json()['segments_limit']

def _get_token() -> str:
    return _get_config_json()['secret']

def _get_audios() -> dict:
    return {} if 'audios' not in _get_config_json() else _get_config_json()['audios']

def _generate_splits(text: str, find: List[str]) -> List[str]:
    r = [ text ]
    prev = None

    for f in find:
        prev = r
        r = []

        regex_pattern = re.compile(r'(?: |^)' + re.escape(f) + r'(?: |$)') # find pattern (sanitized), followed by spaces or begin/end
        for segment in prev:
            split = re.split(regex_pattern, segment)

            more_split = split[0].strip()
            if len(more_split) > 0:
                r.append(more_split)
            for more_split in split[1:]: # skip the first (as we've already added it)
                r.append(f) # as we're on the 2nd index (or higher), it did found a match in between
                more_split = more_split.strip()
                if len(more_split) > 0: # if it's at the end of the string it will produce an empty string
                    r.append(more_split)

    return r

def _splits_to_segments(found: List[str], audios: dict, segment: GeneratedTTSSegment) -> List[TTSSegment]:
    into = []
    synthesizer = segment.synthesizer

    for f in found:
        e = None
        if not f in audios:
            # text
            e = GeneratedTTSSegment(text=f, synthesizer=synthesizer)
        else:
            # audio
            # from route
            audio_entry = audios[f]
            while 'alias' in audio_entry:
                audio_entry = audios[ audio_entry['alias'] ]
            audio_file = random.choice( audio_entry['files'] )
            audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audios/' + audio_file)

            e = PregeneratedTTSSegment(copy_from=audio_path)

        into.append(e)
    return into

def _get_tts_models() -> List[RVCTTSSynthesizer]:
    r = []

    models_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../rvc-tts-webui/weights')
    models = [ f.name for f in os.scandir(models_folder) if f.is_dir() ]
    print(f"[v] Found models in folder: {models}")

    voices = _get_config_json()['voices']
    for voice,data in voices.items():
        model_name = data['model-name']
        if model_name not in models:
            raise ValueError(f"Model {model_name} not found in models folder")

        r.append(RVCTTSSynthesizer(RVCModel(voice, model_name, data['model-voice'])))

    return r

def instantiate(default_synthesizer: TTSSynthesizer = None) -> TwitchTTSBot:
    queue_pre_inference = []
    queue_post_inference = []

    # character limit
    character_limit = _get_character_limit()
    if character_limit is not None:
        async def truncate_input(e: TTSQueueEntry):
            e.segments[0].text = e.segments[0].text[:character_limit]
            return e

        queue_pre_inference.append(pl.task.map(truncate_input))

    models = _get_tts_models()
    # TODO change voices
    
    # replace audios
    audios = _get_audios()
    if len(audios) > 0:
        async def segment_input(e: TTSQueueEntry):
            segments = e.segments[:]
            e.segments.clear() # remove all previous segments

            for segment in segments:
                if not isinstance(segment, GeneratedTTSSegment):
                    raise ValueError("This code wasn't mean to be used with different than text segments")

                splits = _generate_splits(segment.text, list(audios.keys()))
                e.segments += _splits_to_segments(splits, audios, segment) # replace the segment for the new ones
            return e

        queue_pre_inference.append(pl.task.map(segment_input))
    
    segments_limit = _get_segments_limit()
    if segments_limit is not None:
        async def truncate_input(e: TTSQueueEntry):
            e.segments = e.segments[:segments_limit]
            return e

        queue_pre_inference.append(pl.task.map(truncate_input))

    # return the instance
    return TwitchTTSBot.instance(WebServer(secret_token=_get_token()), default_synthesizer if default_synthesizer is not None else models[0], queue_pre_inference=queue_pre_inference, queue_post_inference=queue_post_inference)