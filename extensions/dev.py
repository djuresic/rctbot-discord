import aiohttp
import discord
from discord.ext import commands

import config

from core.mongodb import CLIENT
from core.rct import DatabaseManager, CycleManager, MatchManipulator
from hon.acp2 import ACPClient


class Development(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[config.MONGO_DATABASE_NAME]

    @commands.command()
    @commands.is_owner()
    async def ap(self, ctx, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.add_perks(8198846))

    @commands.command()
    @commands.is_owner()
    async def rp(self, ctx, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.remove_perks(8198846))

    @commands.command()
    @commands.is_owner()
    async def pw(self, ctx, masterserver="rc"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.change_password("lightwalker", "dan787"))

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
    async def t5(self, ctx):
        print(config.LIST_OF_LISTS)

    @commands.command()
    @commands.is_owner()
    async def fixdid(self, ctx, member: discord.Member):
        async with DatabaseManager() as dbm:
            await dbm.fix_discord_id(member)


def setup(bot):
    bot.add_cog(Development(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Development(bot))
    config.LOADED_EXTENSIONS.remove(__loader__.name)
