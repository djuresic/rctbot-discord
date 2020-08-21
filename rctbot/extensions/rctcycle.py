import discord
from discord.ext import commands

import rctbot.config
from rctbot.core.rct import CycleManager


class RCTCycle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: .cycle update x, .cycle distribute y

    # TODO: Send CycleManagerResult().discord_message
    @commands.group()
    @commands.is_owner()
    async def update(self, ctx):
        pass

    @update.command(name="archive")
    async def _uarchive(self, ctx):
        cm = CycleManager()
        await cm.archive_cycle()
        await ctx.send("**Archived** the past cycle in DB.")

    @update.command(name="cycle")
    async def _ucycle(self, ctx):
        cm = CycleManager()
        # TODO: Call archive_cycle() here?
        await cm.new_cycle()
        await ctx.send("***New cycle** set in DB.")

    @update.command(name="games")
    async def _ugames(self, ctx):
        cm = CycleManager()
        await cm.update_games_and_seconds()
        await ctx.send("Updated **games** and **seconds** in DB.")

    @update.command(name="bugs")
    async def _ubugs(self, ctx):
        pass

    @update.command(name="total")
    async def _utotal(self, ctx):
        cm = CycleManager()
        await cm.update_total()
        await ctx.send("Updated **total games**, **total seconds** and **total bugs** in DB.")

    @update.command(name="ranks")
    async def _uranks(self, ctx):
        cm = CycleManager()
        await cm.update_ranks()
        await ctx.send("Updated **ranks** in DB.")

    @update.command(name="tokens")
    async def _utokens(self, ctx):
        cm = CycleManager()
        await cm.update_tokens()
        await ctx.send("Updated **tokens** in DB.")

    @update.command(name="perks")
    async def _uperks(self, ctx):
        cm = CycleManager()
        await ctx.send(await cm.update_perks())

    @commands.group()
    @commands.is_owner()
    async def distribute(self, ctx):
        pass

    @distribute.command(name="tokens")
    async def _dtokens(self, ctx):
        cm = CycleManager()
        success, error = await cm.distribute_tokens()
        # TODO: Handle None.
        await ctx.send(f"Passed:\n{discord.utils.escape_markdown(success)}")
        await ctx.send(f"Failed:\n{discord.utils.escape_markdown(error)}")


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(RCTCycle(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
