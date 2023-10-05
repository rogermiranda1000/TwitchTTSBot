#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from twitchbot import PubSubPointRedemption
from typing import Union

class AutomodManager:
    """
    If AutoMod blocks a message the bot still gets the redemption (before verification).
    However, the bot won't get the `on_channel_points_redemption` until it is validated.

    This class will wait for both events before forwarding the redemption.
    """

    def __init__(self, mod_check_callback: 'Callable[[PubSubPointRedemption], Awaitable[None]]'):
        self._mod_check_callback = mod_check_callback

        self._legacy_pending = []
        self._redeem_pending = []

    async def on_channel_points_redemption(self, user: str, reward_id: str, channel: str):
        # TODO we still don't have a way to fully relate this event with `on_pubsub_channel_points_redemption`;
        #      we'll check the user, id and channel, but we can't relate with the `redemption_id`
        self._legacy_pending.append(LegacyRedeem(user, reward_id))
        await self._search_for_redemption_pairs()

    async def on_pubsub_channel_points_redemption(self, data: PubSubPointRedemption):
        self._redeem_pending.append(data)
        await self._search_for_redemption_pairs()

    async def _search_for_redemption_pairs(self):
        for redeem in self._redeem_pending[:]:
            legacy_match = [ ok for ok in self._legacy_pending if ok == redeem ]
            if len(legacy_match) > 0:
                print(f"[v] Redeem from {redeem.user_login_name} got an ok")

                await self._mod_check_callback(redeem)

                # forwarded; remove from pending
                self._redeem_pending.remove(redeem)
                self._legacy_pending.remove(legacy_match[0])


class LegacyRedeem:
    def __init__(self, user: str, reward: str):
        self._user = user
        self._reward = reward

    @property
    def user(self) -> str:
        return self._user

    @property
    def reward(self) -> str:
        return self._reward

    def __eq__(self, that: Union[LegacyRedeem,PubSubPointRedemption]):
        if isinstance(that, LegacyRedeem):
            return self.user == that.user and self.reward == that.reward
        elif isinstance(that, PubSubPointRedemption):
            # TODO also check channel with `data.get_channel().name`
            return self.user == that.user_login_name and self.reward == that.reward_id

        return False
