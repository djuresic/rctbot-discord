import discord
from discord.ext import commands

import config


class DatabaseNotReady(commands.CheckFailure):
    pass

class NotInWhiteList(commands.CheckFailure):
    pass

class NotATester(commands.CheckFailure): #TO DO: special case in handler
    pass

class GuildOnlyCommand(commands.CheckFailure):
    pass

def database_ready():
    #ctx mandatory positional argument
    async def database_ready_check(ctx):
        if not config.DATABASE_READY:
            raise DatabaseNotReady("Database is not ready!")   
        return True
        #return config.DATABASE_READY
    return commands.check(database_ready_check)

def in_whitelist(whitelist):
    async def in_whitelist_check(ctx):
        if ctx.author.id not in whitelist:
            raise NotInWhiteList("You're not on the whitelist!")
        return True
    return commands.check(in_whitelist_check)

def is_tester():
    async def is_tester_check(ctx):
        if not config.DATABASE_READY:
            raise DatabaseNotReady("Database is not ready!")

        found_id = False
        is_enabled = False

        def checkbox_to_bool(checkbox):
            return checkbox.lower() in ('true', '1')

        for x in config.LIST_OF_LISTS:
            if x[32] == str(ctx.author.id):
                found_id = True
                is_enabled = checkbox_to_bool(x[0])
                break

        return found_id and is_enabled
    return commands.check(is_tester_check)

def guild_only(): #TO DO: this annoyance
    async def guild_only_check(ctx):
        if ctx.message.guild is None:
            raise GuildOnlyCommand("Not allowed in Direct Message!")
        return True
    return commands.check(guild_only_check)

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, NotInWhiteList):
            await ctx.author.send(error)

        if isinstance(error, DatabaseNotReady):
            await ctx.send("{.mention} Slow down speedy, I just woke up. Try *me* again in a few seconds.".format(ctx.author))

        print(error)
        return

def setup(bot):
    bot.add_cog(ErrorHandler(bot))
    print("Error handler ready.")
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)
