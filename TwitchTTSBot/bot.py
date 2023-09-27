#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twitchbot import BaseBot
from twitchbot import PubSubData,PubSubPointRedemption,Message

import re,sys

class TwitchTTSBot(BaseBot):
    async def on_raw_message(self, msg: Message):
        # I swear I tried using `on_pubsub_moderation_action`, but fuck it
        print(">>> " + str(msg))

        # perma: '@room-id=<...>;target-user-id=<...>;tmi-sent-ts=<...> :tmi.twitch.tv CLEARCHAT #<mod> :<banned user>'
        # timeout: '@ban-duration=<timeout [s]>;room-id=<...>;target-user-id=<...>;tmi-sent-ts=<...> :tmi.twitch.tv CLEARCHAT #<mod> :<banned user>'
        timeout = r'^(?:@ban-duration=(\d+);)?.+ CLEARCHAT #(\S+) :(\S+)$'
        timeout_search = re.search(timeout, str(msg))

        if timeout_search:
            self._banned_user(timeout_search.group(3), timeout_search.group(2), sys.maxsize if timeout_search.group(1) is None else int(timeout_search.group(1)))
    
    async def on_pubsub_custom_channel_point_reward(self, _: PubSubData, data: PubSubPointRedemption):
        print(f'{data.user_display_name} redeemed {data.reward_title}')
        print(f'[v] {data.reward_prompt} ; {data.user_input}')
        #if data.reward_title == "Channel point redeem":
        #    pass

    async def on_channel_points_redemption(self, msg: Message, reward: str):
        print(f"[v] Legacy point redeem call: {msg} ; {reward}")
    
    def _banned_user(self, user: str, mod: str, time: int):
        print(f"[v] The user {user} was banned by {mod} ({time})")

def main():
    TwitchTTSBot().run()

if __name__ == '__main__':
    main()