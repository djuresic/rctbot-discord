import rctbot.config

from rctbot.extensions.rct.account import RCTAccount
from rctbot.extensions.rct.bugs import BugReports
from rctbot.extensions.rct.clan import Clan
from rctbot.extensions.rct.cycle import RCTCycle
from rctbot.extensions.rct.extra import ExtraTokensCog
from rctbot.extensions.rct.leaderboard import Leaderboard
from rctbot.extensions.rct.lookup import Lookup
from rctbot.extensions.rct.matchtools import MatchTools
from rctbot.extensions.rct.playtesting import Playtesting
from rctbot.extensions.rct.stats import RCTStats
from rctbot.extensions.rct.usage import HeroUsage
from rctbot.extensions.rct.useradmin import RCTUserAdmin
from rctbot.extensions.rct.welcome import RCTWelcome


def setup(bot):
    bot.add_cog(RCTAccount(bot))
    bot.add_cog(BugReports(bot))
    bot.add_cog(Clan(bot))
    bot.add_cog(RCTCycle(bot))
    bot.add_cog(ExtraTokensCog(bot))
    bot.add_cog(Leaderboard(bot))
    bot.add_cog(Lookup(bot))
    bot.add_cog(MatchTools(bot))
    bot.add_cog(Playtesting(bot))
    bot.add_cog(RCTStats(bot))
    bot.add_cog(HeroUsage(bot))
    bot.add_cog(RCTUserAdmin(bot))
    bot.add_cog(RCTWelcome(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Leaderboard(bot))
    bot.remove_cog(Lookup(bot))
    bot.remove_cog(Playtesting(bot))
    bot.remove_cog(RCTStats(bot))
    bot.remove_cog(HeroUsage(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
