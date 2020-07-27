import binascii
from hashlib import md5, sha256

import asyncio
import aiohttp
import discord
from discord.ext import commands

import utils.phpserialize as phpserialize
import srp

import config


class GameClient:
    def __init__(self, session=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

    # async def __aenter__(self) -> "GameClient":
    async def __aenter__(self):
        await self.authenticate()
        return self

    # async def __aexit__(self, *_) -> None:
    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        await self.session.close()

    async def authenticate(self):
        pass


# pylint: disable=unused-argument, missing-function-docstring
def setup(bot):
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
