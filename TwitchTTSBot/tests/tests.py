import sys
sys.path.append("../")

import unittest
from bot import TwitchTTSBot
from twitchbot import Event,PubSubData,PubSubPointRedemption

class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._bot = TwitchTTSBot().run()

    @classmethod
    def tearDownClass(cls):
        pass # TODO close bot

    def test_redeem(self):
        data = PubSubData({'reward_title': 'TTS', 'user_input': 'This is a test.'})
        self._bot.forward_event(Event.on_pubsub_custom_channel_point_reward, data, PubSubPointRedemption(data))

if __name__ == '__main__':
    unittest.main()