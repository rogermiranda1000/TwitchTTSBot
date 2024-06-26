import unittest
import os, json
from bot import TwitchTTSBot
from twitchbot import Event,PubSubData,PubSubPointRedemption,Message
from twitchbot import forward_event
import asyncio
from time import sleep

import bot_factory

class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._bot = bot_factory.instantiate()
        cls._channel = BotTests.__Channel()
        cls._bot.run_in_async_task()

        async def await_for_bot():
            await asyncio.sleep(15) # TODO get when bot is connected

        cls._loop = asyncio.get_event_loop()
        cls._loop.run_until_complete(await_for_bot())

    @classmethod
    def tearDownClass(cls):
        pass # TODO close bot

    @staticmethod
    def __RedeemId() -> str:
        return "8a7da6dc-cb5c-42da-b522-8601e5126677"

    @staticmethod
    def __Channel() -> str:
        config = None
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs/config.json')) as f:
            config = json.load(f)

        channel = config['channels'][0]
        print(f"[v] Working on channel {channel}")
        return channel

    @staticmethod
    def _GetRedeem(prompt: str, user: str) -> dict:
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
                                \"id\": \"""" + BotTests.__RedeemId() + """\",
                                \"channel_id\": \"35927458\",
                                \"title\": \"""" + TwitchTTSBot._GetRedeemName() + """\",
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

    @staticmethod
    def _GetRedeemData(prompt: str = "This is a test.", user: str = 'userman2') -> PubSubPointRedemption:
        data = PubSubData(BotTests._GetRedeem(prompt, user))
        return PubSubPointRedemption(data)

    @staticmethod
    def _GetLegacyRedeem(prompt: str, user: str, channel: str) -> str:
        return f"@badge-info=;badges=premium/1;color=#00C2CC;custom-reward-id={BotTests.__RedeemId()};display-name={user};emotes=;first-msg=0;flags=;id=66460adc-9eba-4772-9aa1-601c790d74fc;mod=0;returning-chatter=0;room-id=35927458;subscriber=0;tmi-sent-ts=1696674771960;turbo=0;user-id=35927458;user-type= :{user}!{user}@{user}.tmi.twitch.tv PRIVMSG #{channel} :{prompt}"

    @classmethod
    def _GetLegacyRedeemData(cls, prompt: str, user: str, channel: str = None) -> Message:
        if channel is None:
            channel = cls._channel

        return Message(BotTests._GetLegacyRedeem(prompt, user, channel), irc=cls._bot.irc, bot=cls._bot)

    @classmethod
    def _GenerateEvent(cls, redeem_data: PubSubPointRedemption):
        forward_event(Event.on_channel_points_redemption, cls._GetLegacyRedeemData(redeem_data.user_input, redeem_data.user_login_name, cls._channel), redeem_data.reward_id, channel=cls._channel)

        data = redeem_data.data
        forward_event(Event.on_pubsub_custom_channel_point_reward, data, redeem_data, channel=cls._channel)

    def sleep(self, time: int):
        async def sleep_for():
            await asyncio.sleep(time)
        self._loop.run_until_complete(sleep_for())

    def test_redeem(self):
        print("[v] Launching custom event")
        data = BotTests._GetRedeemData()
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(10) # TODO get when bot is done

    def test_empty(self):
        print("[v] Launching custom event (empty)")
        data = BotTests._GetRedeemData("")
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(8) # TODO get when bot is done

    def test_null(self):
        """
        A not-empty request, but the TTS will fail to generate (causing a null response)
        """
        print("[v] Launching custom event (null)")
        data = BotTests._GetRedeemData(": ")
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(8) # TODO get when bot is done

    def test_multiple_redeems(self):
        print("[v] Launching x2 custom event")
        data = BotTests._GetRedeemData("An extensive text will be longer, thus more time-exhaustive.")
        BotTests._GenerateEvent(data)
        data = BotTests._GetRedeemData()
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(20) # TODO get when bot is done

    def test_interrupt(self):
        print("[v] Launching custom event (to be interrupted)")
        data = BotTests._GetRedeemData("An extensive text will be longer, thus more time-exhaustive.", user='to_ban')
        BotTests._GenerateEvent(data)
        
        self.sleep(8) # wait to process and start speaking
        self._loop.run_until_complete(self._bot._banned_user('to_ban', 'rogermiranda1000', 1))

        # don't stop until done
        self.sleep(10) # TODO get when bot is done

    def test_skip(self):
        print("[v] Launching custom event (to be skipped)")
        data = BotTests._GetRedeemData(user='to_ban2')
        BotTests._GenerateEvent(data)
        
        self._loop.run_until_complete(self._bot._banned_user('to_ban2', 'rogermiranda1000', 1))

        # don't stop until done
        self.sleep(15) # TODO get when bot is done

    def test_expired_ban(self):
        print("[v] Launching custom event (x1 to be skipped, x1 to be played)")
        data = BotTests._GetRedeemData('[maniacal laugh]', user='to_ban3')
        BotTests._GenerateEvent(data)
        
        self._loop.run_until_complete(self._bot._banned_user('to_ban3', 'rogermiranda1000', 1))
        
        self.sleep(10) # let it process

        data = BotTests._GetRedeemData("Sorry for that", user='to_ban3')
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(10) # TODO get when bot is done

    def test_automod_block(self):
        print("[v] Launching custom event (x1 to be pre-blocked)")
        data = BotTests._GetRedeemData(user='to_ban4')
        forward_event(Event.on_pubsub_custom_channel_point_reward, data.data, data) # only redeem; no legacy redeem event
        
        self.sleep(10) # let it process

    def test_automod_false_positive(self):
        print("[v] Launching custom event (x1 to be pre-blocked but allowed)")
        data = BotTests._GetRedeemData("I hope this will go through.")
        forward_event(Event.on_pubsub_custom_channel_point_reward, data.data, data)

        self.sleep(10) # let some time

        forward_event(Event.on_channel_points_redemption, BotTests._GetLegacyRedeemData(data.user_input, data.user_login_name), data.reward_id)

        self.sleep(15) # let it process

    def test_automod_bypass(self):
        """
        What if one message gets blocked, and then another is sent? Will the first (blocked) message go through?
        """

        print("[v] Launching custom event (x1 to be pre-blocked, x1 to be played)")
        data = BotTests._GetRedeemData('[maniacal laugh]', user='to_ban5')
        forward_event(Event.on_pubsub_custom_channel_point_reward, data.data, data) # only redeem; no legacy redeem event
        
        self.sleep(10) # let some time

        data = BotTests._GetRedeemData(user='to_ban5')
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(20) # TODO get when bot is done

    def test_automod_bypass_2(self):
        """
        What if two messages gets blocked, and one gets allowed? (None should play, as it's undetermined which one was allowed)
        """

        print("[v] Launching custom event (x2 to be pre-blocked)")
        data = BotTests._GetRedeemData('[maniacal laugh]', user='to_ban6')
        forward_event(Event.on_pubsub_custom_channel_point_reward, data.data, data) # only redeem; no legacy redeem event
        
        self.sleep(10) # let some time

        data = BotTests._GetRedeemData(user='to_ban6')
        forward_event(Event.on_pubsub_custom_channel_point_reward, data.data, data) # only redeem; no legacy redeem event
        
        self.sleep(10) # let some time

        forward_event(Event.on_channel_points_redemption, BotTests._GetLegacyRedeemData(data.user_input, data.user_login_name), data.reward_id)

        # don't stop until done
        self.sleep(20) # TODO get when bot is done


    def test_audios(self):
        print("[v] Launching custom event (audio)")
        data = BotTests._GetRedeemData("[pop]")
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(15) # TODO get when bot is done

    def test_multiple_voices(self):
        print("[v] Launching custom event (multiple voices)")
        data = BotTests._GetRedeemData("Does this work? glados: Yes, it seems to work just fine. nedia: Cool!")
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(20) # TODO get when bot is done

    def test_ignorecase_voices(self):
        print("[v] Launching custom event (custom voice)")
        data = BotTests._GetRedeemData("Broadcast: Attention: this works.")
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(15) # TODO get when bot is done

    def test_custom_synthetizer(self):
        print("[v] Launching custom synthetizer")
        data = BotTests._GetRedeemData("furry: Hello there!")
        BotTests._GenerateEvent(data)

        # don't stop until done
        self.sleep(15) # TODO get when bot is done

if __name__ == '__main__':
    unittest.main()