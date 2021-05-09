import string
import secrets

import discord
from discord.ext import commands

import rctbot.config
from rctbot.core.checks import in_whitelist
from rctbot.hon.acp2 import ACPClient


class TourAdmin(commands.Cog):
    "Tournament administration commands."

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @in_whitelist([146866326378512384, 410169351854096396, 111189137335263232, 295305249877524481, 127605782840737793])
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def tap(self, ctx, *nicknames):
        """Generate and set a new account password for HoNTour Caster accounts used by Tournament Organizers.

        Nicknames can be passed in as space separated commands arguments manually.
        """
        if not nicknames:
            nicknames = ("TourAdmin1", "TourAdmin2", "TourAdmin3")
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for i in range(16))
        await ctx.send(f"Attempting to set password to: ```\n{password}```")
        async with ACPClient(admin=ctx.author, masterserver="ac") as acp:
            for nickname in nicknames:
                await ctx.send(discord.utils.escape_markdown(await acp.change_password(nickname, password)))


def setup(bot):
    bot.add_cog(TourAdmin(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(TourAdmin(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
