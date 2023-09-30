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

from synthesizers.rvc_synthesizer import RVCTTSSynthesizer

class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._bot = TwitchTTSBot.instance(WebServer(), RVCTTSSynthesizer())
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
            "type": "MESSAGE",
            "data": {
                "topic":"channel-points-channel-v1.35927458",
                "message":"""{
                    \"type\": \"reward-redeemed\",
                    \"data\": {
                        \"timestamp\": \"2023-09-28T22:14:08.289959728Z\",
                        \"redemption\": {
                            \"id\": \"66460adc-9eba-4772-9aa1-601c790d74fc\",
                            \"user\": {
                                \"id\": \"35927458\",
                                \"login\": \"userman2\",
                                \"display_name\": \"userman2\"
                            },
                            \"channel_id\": \"35927458\",
                            \"redeemed_at\": \"2023-09-28T22:14:08.289959728Z\",
                            \"reward\": {
                                \"id\": \"8a7da6dc-cb5c-42da-b522-8601e5126677\",
                                \"channel_id\": \"35927458\",
                                \"title\": \"""" + PubSubSubscriberMod._GetRedeemName() + """\",
                                \"prompt\": \"test for pubsub custom reward with texts\",
                                \"cost\": 1,
                                \"is_user_input_required\": true,
                                \"is_sub_only\": false,
                                \"image\": null,
                                \"default_image\": {
                                    \"url_1x\": \"https://static-cdn.jtvnw.net/custom-reward-images/default-1.png\",
                                    \"url_2x\": \"https://static-cdn.jtvnw.net/custom-reward-images/default-2.png\",
                                    \"url_4x\": \"https://static-cdn.jtvnw.net/custom-reward-images/default-4.png\"
                                },
                                \"background_color\": \"#FAB3FF\",
                                \"is_enabled\": true,
                                \"is_paused\": false,
                                \"is_in_stock\": true,
                                \"max_per_stream\": {
                                    \"is_enabled\": false,
                                    \"max_per_stream\": 0
                                },
                                \"should_redemptions_skip_request_queue\": true,
                                \"template_id\": null,
                                \"updated_for_indicator_at\": \"2021-02-05T23:33:10.862461839Z\",
                                \"max_per_user_per_stream\": {
                                    \"is_enabled\": false,
                                    \"max_per_user_per_stream\": 0
                                },
                                \"global_cooldown\": {
                                    \"is_enabled\": false,
                                    \"global_cooldown_seconds\": 0
                                },
                                \"redemptions_redeemed_current_stream\": null,
                                \"cooldown_expires_at\": null
                            },
                            \"user_input\": \"This is a test.\",
                            \"status\":\"FULFILLED\"
                        }
                    }
                }"""
            }
        })
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))


        # don't stop
        self._loop.run_forever()

if __name__ == '__main__':
    unittest.main()