import discord
from discord.ext import commands

import config
from core.checks import is_senior
from core.rct import CycleManager


class RCTCycle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.is_owner()
    async def update(self, ctx):
        pass

    @update.command(name="cycle")
    async def _ucycle(self, ctx):
        async with CycleManager() as cm:
            await cm.new_cycle()
            await ctx.send("***New cycle** set in DB.")

    @update.command(name="games")
    async def _ugames(self, ctx):
        async with CycleManager() as cm:
            await cm.update_games_and_seconds()
            await ctx.send("Updated **games** and **seconds** in DB.")

    @update.command(name="bugs")
    async def _ubugs(self, ctx):
        pass

    @update.command(name="total")
    async def _utotal(self, ctx):
        async with CycleManager() as cm:
            await cm.update_total()
            await ctx.send(
                "Updated **total games**, **total seconds** and **total bugs** in DB."
            )

    @update.command(name="ranks")
    async def _uranks(self, ctx):
        async with CycleManager() as cm:
            await cm.update_ranks()
            await ctx.send("Updated **ranks** in DB.")

    @update.command(name="tokens")
    async def _utokens(self, ctx):
        async with CycleManager() as cm:
            await cm.update_tokens()
            await ctx.send("Updated **tokens** in DB.")

    @commands.group()
    @commands.is_owner()
    async def distribute(self, ctx):
        pass

    @distribute.command(name="tokens")
    async def _dtokens(self, ctx):
        async with CycleManager() as cm:
            success, error = await cm.distribute_tokens()
            await ctx.send(f"Passed:\n{discord.utils.escape_markdown(success)}")
            await ctx.send(f"Failed:\n{discord.utils.escape_markdown(error)}")


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(RCTCycle(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)