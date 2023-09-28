import unittest
from bot import TwitchTTSBot
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
        cls._bot = TwitchTTSBot(WebServer())
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
        data = PubSubData({'reward_title': 'AIden TTS', 'user_input': 'This is a test.', 'user_login_name': 'rogermiranda1000'})
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))


        self._loop.run_forever()

if __name__ == '__main__':
    unittest.main()