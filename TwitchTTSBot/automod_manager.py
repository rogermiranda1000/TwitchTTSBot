#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from twitchbot import PubSubPointRedemption
from typing import Union,Any
import datetime as dt
import asyncio

# template import
from typing import TypeVar,Generic
T = TypeVar('T')

class AutomodManager:
    """
    If AutoMod blocks a message the bot still gets the redemption (before verification).
    However, the bot won't get the `on_channel_points_redemption` until it is validated.

    This class will wait for both events before forwarding the redemption.



    There's 4 different outcomes:

    1. Regular redeem
    t0: Legacy redeem
    t1: Redeem

    2. Interrupted redeem
    t0: Redeem
    ...
    t100: Legacy redeem

    3. Lost redeem + redeem
    t0: Redeem
    ...
    t100: Legacy redeem
    t101: Redeem

    4. x2 lost redeems
    t0: Redeem
    ...
    t100: Redeem
    ...
    t200: Legacy redeem (from unknown)
    """

    MS_MARGIN = 400 # a redeem is expected after less than 500ms since the last "legacy redeem"

    def __init__(self, mod_check_callback: 'Callable[[PubSubPointRedemption], Awaitable[None]]'):
        self._mod_check_callback = mod_check_callback

        self._list_notifier = asyncio.Condition()
        self._legacy_pending = []
        self._redeem_pending = []

    async def loop(self):
        while True:
            async with self._list_notifier:
                if len(self._legacy_pending) == 0:
                    await self._list_notifier.wait()
                else:
                    await asyncio.sleep(0.5) # give some time

            current_time = dt.datetime.now()
            to_check = [ l for l in self._legacy_pending if l.ms_difference(current_time) >= AutomodManager.MS_MARGIN ] # iterate only the messages once you've given the margin for the other event to come
            self._legacy_pending = [ l for l in self._legacy_pending if l.ms_difference(current_time) < AutomodManager.MS_MARGIN ]

            for legacy in to_check:
                await self._search_for_redemption_pairs(legacy)

    async def on_channel_points_redemption(self, user: str, reward_id: str, channel: str):
        # TODO we still don't have a way to fully relate this event with `on_pubsub_channel_points_redemption`;
        #      we'll check the user, id and channel, but we can't relate with the `redemption_id`
        async with self._list_notifier:
            self._legacy_pending.append(TimestampWrapper(LegacyRedeem(user, reward_id)))
            self._list_notifier.notify()

    async def on_pubsub_channel_points_redemption(self, data: PubSubPointRedemption):
        self._redeem_pending.append(TimestampWrapper(data))

    async def _search_for_redemption_pairs(self, legacy: TimestampWrapper[LegacyRedeem]):
        redeem_match = [ ok for ok in self._redeem_pending if ok.object == legacy.object and ok.ms_difference(legacy) < AutomodManager.MS_MARGIN ]
        
        if len(redeem_match) == 0:
            # no close events; check for allowed AutoMod
            redeem_match = [ ok for ok in self._redeem_pending if ok.object == legacy.object ] # TODO what if 2 pending, one prevented and the other allowed?
            if len(redeem_match) > 1:
                # 2 were pending, one got accepted (and we don't know which one is it, so we have to discard both).
                # If by some case one was blocked by AutoMod, and the other one is a regular redeem and got joined in this iteration,
                # we'll play this one in the next iteration.
                redeem_match = [] # TODO instead of discarding it from the "check list" and iterating over and over again the same, remove it from the original list

        if len(redeem_match) > 0:
            print(f"[v] Redeem from {redeem_match[0].object.user_login_name} got an ok")

            await self._mod_check_callback(redeem_match[0].object)

            # forwarded; remove from pending
            self._redeem_pending.remove(redeem_match[0])
            # element from `_legacy_pending` already removed


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

class TimestampWrapper(Generic[T]):
    def __init__(self, o: T):
        self._object = o
        self._timestamp = dt.datetime.now()

    def ms_difference(self, that: Union[TimestampWrapper[Any],dt.datetime]) -> int:
        that_timestamp = None
        if isinstance(that, dt.datetime):
            that_timestamp = that
        elif isinstance(that, TimestampWrapper):
            that_timestamp = that._timestamp

        return abs(int((self._timestamp - that_timestamp).total_seconds() * 1000))

    @property
    def object(self) -> T:
        return self._object

    @property
    def timestamp(self) -> dt.datetime:
        return self._timestamp
