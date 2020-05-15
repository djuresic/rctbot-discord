import discord
from discord.ext import commands

import core.perseverance
import core.config as config


class DatabaseNotReady(commands.CheckFailure):
    pass


class NotInWhiteList(commands.CheckFailure):
    pass


class NotATester(commands.CheckFailure):  # TO DO: special case in handler
    pass


class NotMasterserverAuthenticated(
    commands.CheckFailure
):  # TO DO: special case in handler
    pass


class GuildOnlyCommand(commands.CheckFailure):
    pass


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, NotInWhiteList):
            await ctx.author.send(error)

        if isinstance(error, DatabaseNotReady):
            await ctx.send(
                "{.mention} Slow down speedy, I just woke up. Try *me* again in a few seconds.".format(
                    ctx.author
                )
            )

        if isinstance(error, NotMasterserverAuthenticated):
            await ctx.send(error)

        print(error)
        return


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
    print("Error handler ready.")
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(ErrorHandler(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
