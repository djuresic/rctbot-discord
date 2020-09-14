import collections

import discord
from discord.ext import commands

import rctbot.config
from rctbot.core import checks
from rctbot.core.mongodb import CLIENT
from rctbot.hon.utils import hero_name, cli_hero_name


def chunks(list_, n):
    # https://stackoverflow.com/a/312464/13185424
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(list_), n):
        yield list_[i : i + n]


class HeroUsage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]

    @commands.group(aliases=["u"], invoke_without_command=True)
    @checks.is_senior()
    async def usage(self, ctx):
        pipeline = [
            {"$unwind": "$participants"},
            {"$project": {"_id": 0, "participants.hero": 1}},
        ]
        documents = await (
            self.testing_games.aggregate(pipeline=pipeline, collation={"locale": "en", "strength": 1})
        ).to_list(length=None)
        heroes = [hero_name(document["participants"]["hero"]) for document in documents]
        counter = collections.Counter(heroes)
        unique_picks = len(heroes)
        message = []
        for hero, times in counter.items():
            message.append(f"{hero}: **{times}** ({round((times/unique_picks)*100, 2)}%)")
        message = chunks(sorted(message), 50)
        for chunk in message:
            await ctx.send("\n".join(chunk))
        await ctx.send(f"Total Hero picks: **{unique_picks}**\nDifferent Heroes from Hero Pool: **{len(counter)}**")

    @usage.command(name="hero", aliases=["h"])
    @checks.is_senior()
    async def _usage_hero(self, ctx, *name):
        cli_name = cli_hero_name(" ".join(name))
        pipeline = [
            {"$sort": {"participants.nickname": 1}},
            {"$match": {"participants.hero": cli_name}},
            {"$unwind": "$participants"},
            {"$match": {"participants.hero": cli_name}},
            {"$project": {"_id": 0, "participants.nickname": 1}},
        ]
        documents = await (
            self.testing_games.aggregate(pipeline=pipeline, collation={"locale": "en", "strength": 1})
        ).to_list(length=None)
        players = [document["participants"]["nickname"] for document in documents]
        counter = collections.Counter(players)
        message = []
        for player, times in counter.items():
            message.append(f"{discord.utils.escape_markdown(player)}: **{times}**")
        message = chunks(sorted(message), 50)
        for chunk in message:
            await ctx.send("\n".join(chunk))
        await ctx.send(f"Times picked: **{len(players)}**\nTimes picked by an unique player: **{len(counter)}**")

    @usage.command(name="player", aliases=["p"])
    @checks.is_senior()
    async def _usage_player(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        pipeline = [
            # {"$sort": {"participants.hero": 1}},
            {"$match": {"participants.nickname": nickname}},
            {"$unwind": "$participants"},
            {"$match": {"participants.nickname": nickname}},
            {"$project": {"_id": 0, "participants.hero": 1}},
        ]
        documents = await (
            self.testing_games.aggregate(pipeline=pipeline, collation={"locale": "en", "strength": 1})
        ).to_list(length=None)
        heroes = [hero_name(document["participants"]["hero"]) for document in documents]
        counter = collections.Counter(heroes)
        message = []
        for hero, times in counter.items():
            message.append(f"{hero}: **{times}**")
        message = chunks(sorted(message), 50)
        for chunk in message:
            await ctx.send("\n".join(chunk))
        await ctx.send(f"Total picks: **{len(heroes)}**\nDifferent Heroes picked: **{len(counter)}**")


def setup(bot):
    bot.add_cog(HeroUsage(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(HeroUsage(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
