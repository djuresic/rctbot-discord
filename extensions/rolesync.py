import discord
from discord.ext import commands

import config
from core.checks import is_senior
from core.mongodb import CLIENT

# NOTE: Lots of hardcoded stuff here.


class RoleSynchronization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[config.MONGO_DATABASE_NAME]
        self.testers = self.db[config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]

    @commands.command()
    @is_senior()
    async def rolesync(self, ctx):
        """Sync RCT roles between HoN Official and RCT."""
        # rct_guild = self.bot.get_guild(210131920611311616)
        hon_guild = self.bot.get_guild(735493943025860658)
        rct_acronym_role = discord.utils.get(hon_guild.roles, name="RCT")
        rct_role = discord.utils.get(hon_guild.roles, name="Retail Candidate Tester")
        # srct_role = discord.utils.get(hon_guild.roles, name="Senior Retail Candidate Tester")

        enabled_testers = []
        async for tester in self.testers.find(
            {
                "enabled": True,
                "$or": [{"role": "Tester"}, {"role": "Senior"}],
                "discord_id": {"$not": {"$eq": None}},
            },
            {"_id": 0, "discord_id": 1},
        ):
            enabled_testers.append(tester["discord_id"])
        async for member in hon_guild.fetch_members(limit=None):
            if member.id in enabled_testers and rct_role not in member.roles:
                await member.add_roles(
                    *[rct_acronym_role, rct_role], reason="Synchronized roles with RCT."
                )
            elif member.id not in enabled_testers and rct_role in member.roles:
                await member.remove_roles(
                    *[rct_acronym_role, rct_role], reason="Synchronized roles with RCT."
                )
            else:
                pass
        await ctx.send(
            f"{ctx.author.mention} Synchronized roles with RCT!", delete_after=10.0
        )


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(RoleSynchronization(bot))
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
