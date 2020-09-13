import collections

import aiohttp
import discord
from discord.ext import commands

import rctbot.config

from rctbot.core.mongodb import CLIENT
from rctbot.core.rct import DatabaseManager, MatchManipulator
from rctbot.core import checks
from rctbot.hon.acp2 import ACPClient
from rctbot.hon.masterserver import Client
from rctbot.hon.utils import hero_name, cli_hero_name


def chunks(list_, n):
    # https://stackoverflow.com/a/312464/13185424
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(list_), n):
        yield list_[i : i + n]


class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]

    @commands.command()
    @commands.is_owner()
    async def ap(self, ctx, account_id, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.add_perks(account_id))

    @commands.command()
    @commands.is_owner()
    async def rp(self, ctx, account_id, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.remove_perks(account_id))

    @commands.command()
    @commands.is_owner()
    async def ca(self, ctx, nickname, masterserver="rc"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            account_id, nickname, password = await acp.create_account(nickname)
            await ctx.send(f"Created {nickname} ({account_id}). Use: {password}")

    @commands.command()
    @commands.is_owner()
    async def ta(self, ctx, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.user_test_access(8198846))
            await ctx.send(await acp.toggle_test_access(8198846))
            await ctx.send(await acp.user_test_access(8198846))
            await ctx.send(await acp.toggle_test_access(8198846))
            await ctx.send(await acp.user_test_access(8198846))
            await ctx.send(await acp.toggle_test_access(8198846))
            await ctx.send(await acp.user_test_access(8198846))
            await ctx.send(await acp.toggle_test_access(8198846))
            await ctx.send(await acp.user_test_access(8198846))

    @commands.command()
    @commands.is_owner()
    async def t1(self, ctx):
        async with MatchManipulator() as mp:
            match_ids = [i for i in range(25063, 25165)]
            for match_id in match_ids:
                await mp.insert_match(match_id)
                data = await mp.match_data(match_id)
                if data is not None:
                    await mp.update_match(match_id, data)

    @commands.command()
    @commands.is_owner()
    async def i_am_absolutely_sure_i_want_to_migrate_from_google_sheets(self, ctx):
        async with DatabaseManager() as dbm:
            await ctx.send(await dbm.migrate_spreadsheet_data())
            await dbm.set_testing_account_id()
            await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def i_want_to_standardize_join_dates(self, ctx):
        async with DatabaseManager() as dbm:
            await ctx.send(await dbm.standardize_joined())

    @commands.command()
    @commands.is_owner()
    async def i_want_to_set_super_ids(self, ctx):
        async with DatabaseManager() as dbm:
            await dbm.set_super_id()
            await ctx.send("super ids set")

    @commands.command()
    @commands.is_owner()
    async def t5(self, ctx):
        print(rctbot.config.LIST_OF_LISTS)

    # TODO: Move to a different module.
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

    @commands.command()
    @commands.is_owner()
    async def fixdid(self, ctx, member: discord.Member):
        async with DatabaseManager() as dbm:
            await dbm.fix_discord_id(member)

    @commands.command()
    @commands.is_owner()
    async def mho(self, ctx, nickname: str = "Lightwalker", table: str = "other"):
        async with aiohttp.ClientSession() as session:
            gc = Client("ac", session=session)
            print(await gc.match_history_overview(nickname, table))


def setup(bot):
    bot.add_cog(Development(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Development(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
