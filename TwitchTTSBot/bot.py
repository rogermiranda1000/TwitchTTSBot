#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twitchbot import BaseBot,Event
from twitchbot import PubSubTopics,get_pubsub,PubSubData,PubSubPointRedemption

class TwitchTTSBot(BaseBot):
    async def on_connected(self):
        await get_pubsub().listen_to_channel('CHANNEL_HERE', [PubSubTopics.channel_points],
                                             access_token='PUBSUB_OAUTH_HERE')
    
    async def on_pubsub_custom_channel_point_reward(self, _: PubSubData, data: PubSubPointRedemption):
        print(f'{data.user_display_name} redeemed {data.reward_title}')
        print(f'[v] {data.reward_prompt} ; {data.user_input}')
        #if data.reward_title == "Channel point redeem":
        #    pass

def main():
    TwitchTTSBot().run()

if __name__ == '__main__':
    main()