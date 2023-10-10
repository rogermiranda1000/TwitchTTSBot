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

import importlib
from processing.processing import ProcessingElement,PreProcessingElement,PostProcessingElement

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
        model_name = data['name']
        if model_name not in models:
            raise ValueError(f"Model {model_name} not found in models folder")

        pitch_shift = 0
        if 'pitch-shift' in data:
            pitch_shift = data['pitch-shift']

        r.append(RVCTTSSynthesizer(RVCModel(voice, model_name, data['voice'], pitch_shift=pitch_shift)))

    return r

def _generate_voice_splits(segment: TTSSegment, models: List[RVCTTSSynthesizer]) -> List[TTSSegment]:
    if not isinstance(segment, GeneratedTTSSegment):
        raise ValueError("This function was mean to be used with a single text segment")

    r = [ segment ]
    prev = None

    for model in models:
        prev = r
        r = []

        regex_pattern = re.compile(r'(?: |^)' + re.escape(model.model.alias) + r':(?: |$)', re.IGNORECASE) # find pattern (sanitized), followed by spaces or begin/end
        for segment in prev:
            split = re.split(regex_pattern, segment.text)

            more_split = split[0].strip()
            if len(more_split) > 0:
                r.append(GeneratedTTSSegment(text=more_split, synthesizer=segment.synthesizer)) # as it's in the left-side, use the previous synthesizer
            for more_split in split[1:]: # skip the first (as we've already added it)
                # as we're on the 2nd index (or higher), it did found a match in between
                more_split = more_split.strip()
                if len(more_split) > 0: # if it's at the end of the string it will produce an empty string
                    r.append(GeneratedTTSSegment(text=more_split, synthesizer=model))

    return r

def _append_processing_folder_modifiers(queue_pre_inference: 'List[Partial[pl.task.Stage[T]]]', queue_post_inference: 'List[Partial[pl.task.Stage[T]]]'):
    processing_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processing')
    python_processing_files = [ 'processing.' + f.name[:-len('.py')] for f in os.scandir(processing_folder) if f.is_file() and f.name.endswith('.py') ]
    try:
        python_processing_files.remove('processing.processing') # this is not a custom module
    except ValueError:
        pass

    for python_processing_file in python_processing_files:
        module = importlib.import_module(python_processing_file)

        # TODO pretty sure this can be enhanced somehow
        # TODO check how the twitch bot did it https://github.com/sharkbound/PythonTwitchBotFramework/blob/8eb95864e3744705a057130e8193248328ccabe7/twitchbot/modloader.py#L334
        for attr in dir(module):
            potential_class = getattr(module, attr)
            if type(potential_class) is type and issubclass(potential_class, ProcessingElement):
                if attr == 'PreProcessingElement' or attr == 'PostProcessingElement':
                    continue
                
                print(f"[v] Class {attr} seems to be a ProcessingElement")
                e = potential_class()
                add_to = queue_pre_inference if isinstance(e, PreProcessingElement) else queue_post_inference
                e.add_to_queue(add_to)

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

    # change voices
    async def voice_delimiter(e: TTSQueueEntry):
        e.segments = _generate_voice_splits(e.segments[0], models)
        return e
    queue_pre_inference.append(pl.task.map(voice_delimiter))
    
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

    _append_processing_folder_modifiers(queue_pre_inference, queue_post_inference)

    # return the instance
    return TwitchTTSBot(WebServer(secret_token=_get_token()), default_synthesizer if default_synthesizer is not None else models[0], queue_pre_inference=queue_pre_inference, queue_post_inference=queue_post_inference)