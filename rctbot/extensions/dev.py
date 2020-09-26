import aiohttp
import discord
from discord.ext import commands

import rctbot.config

from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.core.rct import MatchManipulator
from rctbot.core.rct.migration import DatabaseManager

# from rctbot.core.paginator import EmbedPaginatorSession
# from rctbot.core.utils import chunks

from rctbot.hon.acp2 import ACPClient
from rctbot.hon.masterserver import Client


class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_games = self.db[rctbot.config.MONGO_TESTING_GAMES_COLLECTION_NAME]
        self.testing_bugs = self.db[rctbot.config.MONGO_TESTING_BUGS_COLLECTION_NAME]
        self.testing_cycles = self.db[rctbot.config.MONGO_TESTING_CYCLES_COLLECTION_NAME]

    @commands.command()
    @commands.is_owner()
    async def pgbb(self, ctx, cycle_id: int):
        cycle = await self.testing_cycles.find_one({"_id": cycle_id}, {"games": 1, "bugs": 1})
        await self.testing_games.insert_many(cycle["games"])
        await self.testing_bugs.insert_many(cycle["bugs"])

    @commands.command()
    @commands.is_owner()
    async def addextra(self, ctx, amount: int):
        result = await self.testers.update_many(
            {"enabled": True, "$or": [{"games": {"$gte": 1}}, {"bugs": {"$gte": 1}}],}, {"$set": {"extra": amount}},
        )
        if result.acknowledged:
            await ctx.send(f"Found {result.matched_count} and updated {result.modified_count} members' extra amount.")
        await ctx.send(f"Could not update perks status!")

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
