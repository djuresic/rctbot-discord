from __future__ import annotations

import discord
from discord.ext import commands

import rctbot.config
from rctbot.core import checks
from rctbot.core.rct import BugReport, BugReportManager
from rctbot.core.driver import AsyncDatabaseHandler


class BugReports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_client = AsyncDatabaseHandler.client
        self.db = self.db_client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]

    @commands.group(aliases=["bug", "b"])
    @checks.is_senior()
    async def bugs(self, ctx):
        pass

    @bugs.command(name="add", aliases=["+"])
    async def _bugs_add(self, ctx, nickname: str):
        nickname = nickname.replace("\\", "")
        if not (
            reporter := await self.testers.find_one(
                {"nickname": nickname},
                {
                    "_id": 0,
                    "nickname": 1,
                    "account_id": 1,
                    "super_id": 1,
                    "testing_account_id": 1,
                    "testing_super_id": 1,
                },
                collation={"locale": "en", "strength": 1},
            )
        ):
            return await ctx.send(
                f"{ctx.author.mention} Could not find {discord.utils.escape_markdown(nickname)} in testers!",
                delete_after=8.0,
            )
        bug_report = BugReport(reporter)
        manager = BugReportManager()
        await ctx.send(await manager.insert(bug_report))


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(BugReports(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
