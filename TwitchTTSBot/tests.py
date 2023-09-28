import unittest
from bot import TwitchTTSBot
from mods.pubsub_subscribe import PubSubSubscriberMod
from twitchbot import Event,PubSubData,PubSubPointRedemption
from twitchbot import forward_event
import asyncio
from time import sleep

import sys
sys.path.append("../audio-server")
from webserver import WebServer

class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._bot = TwitchTTSBot.instance(WebServer())
        cls._bot.run_in_async_task()

        async def await_for_bot():
            await asyncio.sleep(15) # TODO get when bot is connected

        cls._loop = asyncio.get_event_loop()
        cls._loop.run_until_complete(await_for_bot())

    @classmethod
    def tearDownClass(cls):
        pass # TODO close bot

    def test_redeem(self):
        print("[v] Launching custom event")
        data = PubSubData({
    "type": "reward-redeemed",
    "data": {
        "timestamp": "2019-11-12T01:29:34.98329743Z",
        "redemption": {
            "id": "9203c6f0-51b6-4d1d-a9ae-8eafdb0d6d47",
            "user": {
                "id": "30515034",
                "login": "davethecust",
                "display_name": "davethecust"
            },
            "channel_id": "30515034",
            "redeemed_at": "2019-12-11T18:52:53.128421623Z",
            "reward": {
                "id": "6ef17bb2-e5ae-432e-8b3f-5ac4dd774668",
                "channel_id": "30515034",
                "title": PubSubSubscriberMod._GetRedeemName(),
                "prompt": "TTS read message\n",
                "cost": 10,
                "is_user_input_required": True,
                "is_sub_only": False,
                "image": {
                    "url_1x": "https://static-cdn.jtvnw.net/custom-reward-images/30515034/6ef17bb2-e5ae-432e-8b3f-5ac4dd774668/7bcd9ca8-da17-42c9-800a-2f08832e5d4b/custom-1.png",
                    "url_2x": "https://static-cdn.jtvnw.net/custom-reward-images/30515034/6ef17bb2-e5ae-432e-8b3f-5ac4dd774668/7bcd9ca8-da17-42c9-800a-2f08832e5d4b/custom-2.png",
                    "url_4x": "https://static-cdn.jtvnw.net/custom-reward-images/30515034/6ef17bb2-e5ae-432e-8b3f-5ac4dd774668/7bcd9ca8-da17-42c9-800a-2f08832e5d4b/custom-4.png"
                },
                "default_image": {
                    "url_1x": "https://static-cdn.jtvnw.net/custom-reward-images/default-1.png",
                    "url_2x": "https://static-cdn.jtvnw.net/custom-reward-images/default-2.png",
                    "url_4x": "https://static-cdn.jtvnw.net/custom-reward-images/default-4.png"
                },
                "background_color": "#00C7AC",
                "is_enabled": True,
                "is_paused": False,
                "is_in_stock": True,
                "max_per_stream": { "is_enabled": False, "max_per_stream": 0 },
                "should_redemptions_skip_request_queue": True
            },
            "user_input": "This is a test.",
            "status": "FULFILLED"
        }
    }
})
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))


        # don't stop
        self._loop.run_forever()

if __name__ == '__main__':
    unittest.main()