import discord
from discord.ext import commands

import config
from core.checks import is_senior
from hon.acp2 import ACPClient


class Clan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["c"])
    @is_senior()
    async def clan(self, ctx):
        pass

    @clan.command(name="invite", aliases=["i", "add"])
    async def _clan_invite(self, ctx, nickname, clan_tag=None, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.clan_invite(nickname, clan_tag))

    @clan.command(name="remove", aliases=["r", "kick"])
    async def _clan_remove(self, ctx, nickname, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.clan_remove(nickname))

    @clan.command(name="promote", aliases=["p"])
    async def _clan_promote(self, ctx, nickname, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.clan_promote(nickname))

    @clan.command(name="demote", aliases=["d"])
    async def _clan_demote(self, ctx, nickname, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.clan_demote(nickname))

    @clan.command(name="crown", aliases=["c"])
    async def _clan_crown(self, ctx, nickname, masterserver="ac"):
        async with ACPClient(admin=ctx.author, masterserver=masterserver) as acp:
            await ctx.send(await acp.clan_crown(nickname))


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(Clan(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
