#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
sys.path.append("../audio-server")
from audioserver import AudioServer

from tts_queue import TTSQueue
import pypeln as pl
from pypeln.utils import Partial,T
from typing import List
from twitchbot import BaseBot,Message,Channel
from twitchbot import PubSubTopics,get_pubsub,PubSubData,PubSubPointRedemption
from synthesizers.synthesizer import TTSSynthesizer

import re,sys,json

class TwitchTTSBot(BaseBot):
    def __init__(self, web: AudioServer, synthesizer: TTSSynthesizer, queue_pre_inference: List[Partial[pl.task.Stage[T]]] = None, queue_post_inference: List[Partial[pl.task.Stage[T]]] = None):
        super().__init__()
        self._web = web
        self._queue = TTSQueue(self._web, synthesizer, queue_pre_inference, queue_post_inference)

        self._redeem_name = TwitchTTSBot._GetRedeemName()

    def run(self):
        loop = self._get_event_loop()
        loop.run_until_complete(self._web.start()) # start the website
        super().run() # start (and keep running) the bot

    def run_in_async_task(self):
        loop = self._get_event_loop()
        loop.run_until_complete(self._web.start()) # start the website
        super().run_in_async_task() # start the bot

    async def shutdown(self):
        await self._web.shutdown()
        await super().shutdown()

    async def on_connected(self):
        access_token = TwitchTTSBot.__GetAccessToken()
        await get_pubsub().listen_to_channel(access_token[0], [ PubSubTopics.channel_points ], access_token=access_token[1])

    async def on_raw_message(self, msg: Message):
        #print(">>> " + str(msg))

        # perma: '@room-id=<...>;target-user-id=<...>;tmi-sent-ts=<...> :tmi.twitch.tv CLEARCHAT #<channel> :<banned user>'
        # timeout: '@ban-duration=<timeout [s]>;room-id=<...>;target-user-id=<...>;tmi-sent-ts=<...> :tmi.twitch.tv CLEARCHAT #<channel> :<banned user>'
        timeout = r'^(?:@ban-duration=(\d+);)?.+ CLEARCHAT #(\S+) :(\S+)$'
        timeout_search = re.search(timeout, str(msg))

        if timeout_search:
            await self._banned_user(timeout_search.group(3), timeout_search.group(2), sys.maxsize if timeout_search.group(1) is None else int(timeout_search.group(1)))

    async def on_channel_points_redemption(self, msg: Message, reward: str):
        print(f"[v] Legacy point redeem call: {msg} ({reward})")
        # <user> redeemed reward <reward ID> in #<channel>
    
    async def on_pubsub_custom_channel_point_reward(self, _: PubSubData, data: PubSubPointRedemption):
        print(f"[v] Point redeem call: {data.reward_title}, '{data.user_input}' (by {data.user_login_name})")
        print(str(data.redemption_id) + ' reward: ' + str(data.reward_id))

        if data.reward_title == self._redeem_name:
            if len(data.user_input.strip()) > 0:
                print(f"[v] The user {data.user_login_name} request the following TTS message: '{data.user_input}'")
                await self._queue.enqueue(data.user_login_name, data.user_input)
    
    async def _banned_user(self, user: str, channel: str, time: int):
        print(f"[v] The user {user} was banned on {channel} ({time}s)")
        await self._queue.erase(user)

    @staticmethod
    def __GetAccessToken() -> Tuple[str,str]:
        config = None
        with open('configs/config.json') as f:
            config = json.load(f)

        return (config['channels'][0], config['pubsub'])

    @staticmethod
    def _GetRedeemName() -> str:
        config = None
        with open('configs/config.json') as f:
            config = json.load(f)

        return config['redeem']

def main():
    import bot_factory
    bot_factory.instantiate().run()

if __name__ == '__main__':
    main()