#!/usr/bin/env python

"""
RCTBot A Discord bot with Heroes of Newerth integration.
Copyright (C) 2020–2021  Danijel Jurešić

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# TODO: Configuration variables for emojis and URLs.
# Cleanup needed.

import os
import asyncio

import discord
from hypercorn.config import Config
from hypercorn.asyncio import serve
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # FIXME

bind_v4 = f'{os.getenv("HOST", "127.0.0.1")}:{os.getenv("PORT", "8000")}'  # Defaults are already Hypercorn defaults.
config = Config()
config.bind = [bind_v4]

if __name__ == "__main__":
    import rctbot
    from rctbot.api.app import app, API

    bot = rctbot.get_bot()

    # TODO: Get this out of here.
    @bot.event
    async def on_ready():
        print(
            "{0} ({0.id}) reporting for duty from {1}! All shall respect the law that is my {2}!".format(
                bot.user, bot.platform, rctbot.config.CONFIG_FILE
            )
        )
        watching = discord.Activity(name="Heroes of Newerth", type=discord.ActivityType.watching)
        # streaming = discord.Streaming(platform="Twitch", name="Heroes of Newerth", game="Heroes of Newerth", url="https://www.twitch.tv/", twitch_name="")
        await bot.change_presence(activity=watching, status=discord.Status.dnd, afk=False)
        print("------")

    # Sigh...
    API.bot = bot
    loop = asyncio.get_event_loop()
    loop.create_task(serve(app, config))

    bot.run()
