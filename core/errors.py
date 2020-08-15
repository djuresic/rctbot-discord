from discord.ext import commands

import config

# TODO: Cleanup needed.


class DatabaseNotReady(commands.CheckFailure):
    pass


class NotInWhiteList(commands.CheckFailure):
    pass


class NotATester(commands.CheckFailure):  # TODO: special case in handler
    pass


class NotMasterserverAuthenticated(commands.CheckFailure):  # TODO: special case in handler
    pass


class NotRCTGuild(commands.CheckFailure):
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
                "{.mention} Slow down speedy, I just woke up. Try *me* again in a few seconds.".format(ctx.author)
            )

        if isinstance(error, NotMasterserverAuthenticated):
            await ctx.send(error)

        print(error)
        return


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
    print("Error handler ready.")
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(ErrorHandler(bot))
    config.LOADED_EXTENSIONS.remove(__loader__.name)
