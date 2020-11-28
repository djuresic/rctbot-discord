import rctbot.config

from rctbot.extensions.hon.official import HoNOfficial
from rctbot.extensions.hon.officialmentions import MentionsTemp
from rctbot.extensions.hon.stats import HoNStats


def setup(bot):
    bot.add_cog(HoNOfficial(bot))
    bot.add_cog(MentionsTemp(bot))
    bot.add_cog(HoNStats(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(MentionsTemp(bot))
    bot.remove_cog(HoNStats(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
