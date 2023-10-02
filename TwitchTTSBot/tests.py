import unittest
from bot import TwitchTTSBot
from mods.pubsub_subscribe import PubSubSubscriberMod
from twitchbot import Event,PubSubData,PubSubPointRedemption
from twitchbot import forward_event
import asyncio
from time import sleep

import bot_factory

class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._bot = bot_factory.instantiate()
        cls._bot.run_in_async_task()

        async def await_for_bot():
            await asyncio.sleep(15) # TODO get when bot is connected

        cls._loop = asyncio.get_event_loop()
        cls._loop.run_until_complete(await_for_bot())

    @classmethod
    def tearDownClass(cls):
        pass # TODO close bot

    @staticmethod
    def _GetRedeem(prompt: str = "This is a test.", user: str = 'userman2') -> dict:
        return {
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
                                \"login\": \"""" + user + """\",
                                \"display_name\": \"""" + user + """\"
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
                            \"user_input\": \"""" + prompt + """\",
                            \"status\":\"FULFILLED\"
                        }
                    }
                }"""
            }
        }

    def sleep(self, time: int):
        async def sleep_for():
            await asyncio.sleep(time)
        self._loop.run_until_complete(sleep_for())

    def test_redeem(self):
        print("[v] Launching custom event")
        data = PubSubData(BotTests._GetRedeem())
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))

        # don't stop until done
        self.sleep(10) # TODO get when bot is done

    def test_multiple_redeems(self):
        print("[v] Launching x2 custom event")
        data = PubSubData(BotTests._GetRedeem("An extensive text will be longer, thus more time-exhaustive."))
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))
        data = PubSubData(BotTests._GetRedeem())
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))

        # don't stop until done
        self.sleep(20) # TODO get when bot is done

    def test_interrupt(self):
        print("[v] Launching custom event (to be interrupted)")
        data = PubSubData(BotTests._GetRedeem("An extensive text will be longer, thus more time-exhaustive.", user='to_ban'))
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))
        
        self.sleep(8) # wait to process and start speaking
        self._loop.run_until_complete(self._bot._banned_user('to_ban', 'rogermiranda1000', 1))

        # don't stop until done
        self.sleep(10) # TODO get when bot is done

    def test_skip(self):
        print("[v] Launching custom event (to be skipped)")
        data = PubSubData(BotTests._GetRedeem(user='to_ban2'))
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))
        
        self._loop.run_until_complete(self._bot._banned_user('to_ban2', 'rogermiranda1000', 1))

        # don't stop until done
        self.sleep(15) # TODO get when bot is done

    def test_audios(self):
        print("[v] Launching custom event (audio)")
        data = PubSubData(BotTests._GetRedeem("[pop]"))
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))

        # don't stop until done
        self.sleep(15) # TODO get when bot is done

    def test_multiple_voices(self):
        print("[v] Launching custom event (multiple voices)")
        data = PubSubData(BotTests._GetRedeem("Does this work? glados: Yes, it seems to work just fine."))
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))

        # don't stop until done
        self.sleep(20) # TODO get when bot is done

if __name__ == '__main__':
    unittest.main()