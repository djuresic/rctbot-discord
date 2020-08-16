import aiohttp
import discord
from discord.ext import commands

import config
from core.checks import is_senior
from core.rct import TesterManager


class RCTUserAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["ua", "useradmin"])
    @commands.is_owner()
    async def user_admin(self, ctx):
        pass

    @user_admin.command(name="add")
    async def _ua_add(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        manager = TesterManager()
        await ctx.send((await manager.add_tester(nickname)).discord_message)

    @user_admin.command(name="reinstate")
    async def _ua_reinstate(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        manager = TesterManager()
        await ctx.send((await manager.reinstate_tester(nickname)).discord_message)

    @user_admin.command(name="remove")
    async def _ua_remove(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        manager = TesterManager()
        await ctx.send((await manager.remove_tester(nickname)).discord_message)

    @user_admin.command(name="link")
    async def _ua_link(self, ctx, member: discord.Member):
        manager = TesterManager()
        await ctx.send((await manager.link_discord(member)).discord_message)


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(RCTUserAdmin(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
