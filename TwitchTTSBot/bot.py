#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append("../audio-server")
from audioserver import AudioServer

from tts_queue import TTSQueue
from synthesizers.rvc_synthesizer import RVCTTSSynthesizer
from twitchbot import BaseBot,Message

import re,sys

class TwitchTTSBot(BaseBot):
    def __init__(self, web: AudioServer):
        super().__init__()
        self._web = web
        self._queue = TTSQueue(self._web, RVCTTSSynthesizer())

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

    async def on_raw_message(self, msg: Message):
        # I swear I tried using `on_pubsub_moderation_action`, but fuck it
        print(">>> " + str(msg))

        # perma: '@room-id=<...>;target-user-id=<...>;tmi-sent-ts=<...> :tmi.twitch.tv CLEARCHAT #<mod> :<banned user>'
        # timeout: '@ban-duration=<timeout [s]>;room-id=<...>;target-user-id=<...>;tmi-sent-ts=<...> :tmi.twitch.tv CLEARCHAT #<mod> :<banned user>'
        timeout = r'^(?:@ban-duration=(\d+);)?.+ CLEARCHAT #(\S+) :(\S+)$'
        timeout_search = re.search(timeout, str(msg))

        if timeout_search:
            await self._banned_user(timeout_search.group(3), timeout_search.group(2), sys.maxsize if timeout_search.group(1) is None else int(timeout_search.group(1)))

    async def on_channel_points_redemption(self, msg: Message, reward: str):
        print(f"[v] Legacy point redeem call: {msg}")
    
    async def _banned_user(self, user: str, mod: str, time: int):
        print(f"[v] The user {user} was banned by {mod} ({time})")
        await self._queue.erase(user)

def main():
    TwitchTTSBot(AudioServer()).run()

if __name__ == '__main__':
    main()