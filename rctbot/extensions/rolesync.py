from __future__ import annotations

from typing import List, Tuple

import discord
from discord.ext import commands, tasks

import rctbot.config
from rctbot.core import checks
from rctbot.core.mongodb import CLIENT

# NOTE: Lots of hardcoded stuff here.


class RoleSynchronization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CLIENT[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.update_volunteers.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.update_volunteers.cancel()  # pylint: disable=no-member

    async def _get_testers(self) -> Tuple[List[int], List[int]]:
        testers = []
        senior_testers = []
        async for tester in self.testers.find(
            {"enabled": True, "$or": [{"role": "Tester"}, {"role": "Senior"}], "discord_id": {"$not": {"$eq": None}},},
            {"_id": 0, "role": 1, "discord_id": 1},
        ):
            if tester["role"] != "Tester":
                senior_testers.append(tester["discord_id"])
            else:
                testers.append(tester["discord_id"])
        return testers, senior_testers

    # update_volunteers
    @tasks.loop(minutes=60.0)
    async def update_volunteers(self):
        """Sync roles between HoN volunteer positions and their Discord servers and HoN Official."""
        # rct_guild = self.bot.get_guild(210131920611311616)
        hon_guild = self.bot.get_guild(735493943025860658)
        rct_acronym_role = discord.utils.get(hon_guild.roles, name="RCT")
        rct_role = discord.utils.get(hon_guild.roles, name="Retail Candidate Tester")
        srct_role = discord.utils.get(hon_guild.roles, name="Senior Retail Candidate Tester")

        testers, senior_testers = await self._get_testers()
        active_members = testers + senior_testers
        async for member in hon_guild.fetch_members(limit=None):
            # Retail Canidate Testers
            if member.id in active_members:
                # None -> RCT
                if member.id in testers and rct_acronym_role not in member.roles:
                    await member.add_roles(*[rct_acronym_role, rct_role], reason="Synchronized roles with RCT.")
                # None -> SRCT
                elif member.id in senior_testers and rct_acronym_role not in member.roles:
                    await member.add_roles(*[rct_acronym_role, srct_role], reason="Synchronized roles with RCT.")
                # SRCT -> RCT
                elif member.id in testers and srct_role in member.roles:
                    await member.add_roles(rct_role, reason="Synchronized roles with RCT.")
                    await member.remove_roles(srct_role, reason="Synchronized roles with RCT.")
                # RCT -> SRCT
                elif member.id in senior_testers and rct_role in member.roles:
                    await member.add_roles(srct_role, reason="Synchronized roles with RCT.")
                    await member.remove_roles(rct_role, reason="Synchronized roles with RCT.")
                # None
                else:
                    pass
            else:
                # RCT -> None
                if rct_role in member.roles:
                    await member.remove_roles(*[rct_acronym_role, rct_role], reason="Synchronized roles with RCT.")
                # SRCT -> None
                elif srct_role in member.roles:
                    await member.remove_roles(*[rct_acronym_role, srct_role], reason="Synchronized roles with RCT.")
                # None
                else:
                    pass

    @commands.command()
    @checks.is_senior()
    async def rolesync(self, ctx):
        self.update_volunteers.restart()  # pylint: disable=no-member
        await ctx.send(f"{ctx.author.mention} Restarted update_volunteers", delete_after=10.0)


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(RoleSynchronization(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
