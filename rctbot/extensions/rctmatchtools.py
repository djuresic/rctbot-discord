from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

import discord
from discord.ext import tasks, commands

import rctbot.config
from rctbot.core import checks
from rctbot.core.utils import chunks
from rctbot.core.driver import CLIENT
from rctbot.core.rct import MatchManipulator


class MatchTools(commands.Cog):
    # TODO: rct.MatchManipulator.last_fetched
    last_fetched: Union[datetime, discord.Embed.Empty] = discord.Embed.Empty

    def __init__(self, bot):
        self.bot = bot
        self.db_client = CLIENT
        self.db = self.db_client[rctbot.config.MONGO_DATABASE_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.auto_fetch.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.auto_fetch.cancel()  # pylint: disable=no-member

    @tasks.loop(minutes=69.0)
    async def auto_fetch(self):
        games = await (self.testing_games.find({"retrieved": False}, {"_id": 0, "match_id": 1})).to_list(length=None)

        async with MatchManipulator(masterserver="rc") as mm:
            for game in games:
                data = await mm.match_data(game["match_id"])
                await mm.update_match(game["match_id"], data)

        MatchTools.last_fetched = datetime.now(timezone.utc)

    @auto_fetch.before_loop
    async def before_auto_fetch(self):
        print("RCT match data Auto Fetch task started.")

    @auto_fetch.after_loop
    async def after_auto_fetch(self):
        print("RCT match data Auto Fetch task stopped.")

    @commands.group(aliases=["m"])
    @checks.is_senior()
    async def match(self, ctx):
        # TODO: Match stats when ID is passed.
        pass

    @match.group(name="insert", aliases=["i", "add", "+"], invoke_without_command=True)
    async def _match_insert(self, ctx, match_id: str):
        if match_id.isdigit():
            await ctx.send((await MatchManipulator.insert_match(match_id)))

    @_match_insert.command(name="range")
    async def _match_insert_range(self, ctx, first: int, last: int):
        results = []
        for match_id in range(first, last + 1):
            results.append((await MatchManipulator.insert_match(match_id)))
        results = chunks(results, 25)
        for chunk in results:
            await ctx.send("\n".join(chunk))

    # NOTE: Just in case someone tries to use it this way.
    @_match_insert.command(name="id")
    async def _match_insert_id(self, ctx, match_id: str):
        if match_id.isdigit():
            await ctx.send((await MatchManipulator.insert_match(match_id)))


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(MatchTools(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
