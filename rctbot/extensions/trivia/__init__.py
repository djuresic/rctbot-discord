import rctbot.config

from rctbot.extensions.trivia.game import TriviaGame
from rctbot.extensions.trivia.admin import TriviaAdmin


def setup(bot):
    bot.add_cog(TriviaGame(bot))
    bot.add_cog(TriviaAdmin(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(TriviaGame(bot))
    bot.remove_cog(TriviaAdmin(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
