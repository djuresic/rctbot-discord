import discord
from discord.ext import commands

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.core.checks import is_tester
from rctbot.core.errors import NotATester
from rctbot.core.logging import record_usage
from rctbot.hon.acp2 import ACPClient


class RCTAccount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.changing_pw = "Someone you should tell Lightwalker about"

    @commands.command(aliases=["pw"])
    @is_tester()
    @commands.dm_only()
    @commands.before_invoke(record_usage)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def password(self, ctx):
        self.changing_pw = ctx.author
        tester = await self.testers.find_one({"discord_id": ctx.author.id}, {"_id": 0, "nickname": 1})
        self.changing_pw = tester["nickname"]
        if not tester:
            return await ctx.send("You are not a tester!")
        await ctx.send(
            f'Enter a new test client password for **{discord.utils.escape_markdown(tester["nickname"])}**:'
        )
        try:
            password = await self.bot.wait_for(
                "message",
                check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                timeout=45.0,
            )
        except:
            return await ctx.send("You took too long. Please use the command again if you wish to continue.")
        async with ACPClient(admin=ctx.author, masterserver="rc") as acp:
            await ctx.send(
                discord.utils.escape_markdown(await acp.change_password(tester["nickname"], password.content))
            )

    # TODO: Handle PrivateMessageOnly globally.
    @password.error
    async def password_error(self, ctx, error):
        if isinstance(error, NotATester):
            await ctx.send(f"{ctx.author.mention} You are not a tester!", delete_after=8.0)
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(f"{ctx.author.mention} {error}", delete_after=8.0)
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                (
                    f"{ctx.author.mention} **{discord.utils.escape_markdown(self.changing_pw)}** is using this command!"
                    f" It can be used only once per tester concurrently."
                ),
                delete_after=8.0,
            )
        # raise error


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(RCTAccount(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
