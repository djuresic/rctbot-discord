import random

import rctbot.config
from discord.ext import commands


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, low: int, high: int):
        """Let's roll the dice!"""
        result = random.randint(low, high)
        await ctx.send("{0} rolled {1} {2} and got **{3}**.".format(ctx.message.author.mention, low, high, result))


def setup(bot):
    bot.add_cog(Gambling(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Gambling(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
