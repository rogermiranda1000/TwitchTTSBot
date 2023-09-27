from twitchbot import Mod
from twitchbot import PubSubTopics,get_pubsub,PubSubData,PubSubPointRedemption,PubSubModerationAction
import json
from typing import Tuple

class PubSubSubscriberMod(Mod):
    async def on_connected(self):
        access_token = PubSubSubscriberMod.__GetAccessToken()
        await get_pubsub().listen_to_channel(access_token[0], [ PubSubTopics.channel_points,PubSubTopics.community_channel_points ], access_token=access_token[1])

    @staticmethod
    def __GetAccessToken() -> Tuple[str,str]:
        config = None
        with open('configs/config.json') as f:
            config = json.load(f)

        return (config['channels'][0], config['pubsub'])

    # only needed in most cases for verifying a connection
    async def on_pubsub_received(self, raw: 'PubSubData'):
        # this should print any errors received from twitch
        print(raw.raw_data)
    
    async def on_pubsub_custom_channel_point_reward(self, _: PubSubData, data: PubSubPointRedemption):
        print(f'{data.user_display_name} redeemed {data.reward_title}')
        print(f'[v] {data.reward_prompt} ; {data.user_input}')
        #if data.reward_title == "Channel point redeem":
        #    pass