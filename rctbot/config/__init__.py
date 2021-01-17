"""
RCTBot A Discord bot with Heroes of Newerth integration.
Copyright (C) 2020–2021  Danijel Jurešić

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import platform

from rctbot.core.driver import DatabaseHandler

# TODO: Still a lot of work to do...

# Detect if deployed on Heroku. NOTE: This is not currently in use.
HEROKU_DEPLOYED = bool("DYNO" in os.environ)

# TODO: WIP; Partial low priority


class PartialConfiguration:  # name isn't great tbh KEKW
    pass


class DiscordConfiguration(PartialConfiguration):
    """
    RCTBot Discord configuration.
    """

    def __init__(self, document: dict):
        self.token = os.getenv("DISCORD_TOKEN", None)
        self.home = document["DISCORD"]["RCT_GUILD_ID"]


class MongoDBConfiguration(PartialConfiguration):
    """
    RCTBot MongoDB configuration.
    """

    rct = "rct"
    testers = "testers"
    games = "testing_games"
    bugs = "testing_bugs"
    cycles = "testing_cycles"
    extra = "testing_extra"


class HoNConfiguration(PartialConfiguration):
    """
    RCTBot HoN configuration.
    """

    pass


class Configuration:
    """
    RCTBot configuration.
    """

    release_stage = None

    db = DatabaseHandler.client["rctbot"]
    collection = db["config"]
    document = {}

    discord = None
    mongodb = None
    hon = None

    @staticmethod
    def load(release_stage: str) -> None:
        """Load new configuration.

        Args:
            release_stage (str): Release stage.

        Raises:
            Exception: Invalid stage or no configuration found.
        """
        document = Configuration.collection.find_one({"release_stage": release_stage})
        if document is None:
            raise Exception("Invalid stage or no configuration found!")
        Configuration.release_stage = release_stage
        Configuration.document = document

        Configuration.discord = DiscordConfiguration(document)
        Configuration.mongodb = MongoDBConfiguration()
        Configuration.hon = HoNConfiguration()

    @staticmethod
    def reload() -> None:
        """Reload current configuration.

        Raises:
            Exception: No configuration found.
        """
        document = Configuration.collection.find_one({"release_stage": Configuration.release_stage})
        if document is None:
            raise Exception("No configuration found!")
        Configuration.document = document

        # TODO: Partial.


config = Configuration
# Loads dev config on Windows by default.
if "Windows" in platform.system():
    os.environ["PYTHONASYNCIODEBUG"] = "1"
    # stage, release_stage, environment, tier
    config.load("dev")
else:
    config.load("prod")

CONFIG_DOCUMENT = config.document


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", None)
DISCORD_RCT_GUILD_ID = CONFIG_DOCUMENT["DISCORD"]["RCT_GUILD_ID"]  # TODO: Home
DISCORD_NOTES_CHANNEL_ID = CONFIG_DOCUMENT["DISCORD"]["NOTES_CHANNEL_ID"]
DISCORD_BOT_LOG_CHANNEL_ID = CONFIG_DOCUMENT["DISCORD"]["BOT_LOG_CHANNEL_ID"]
DISCORD_WELCOME_CHANNEL_ID = CONFIG_DOCUMENT["DISCORD"]["WELCOME_CHANNEL_ID"]
DISCORD_WHITELIST_IDS = CONFIG_DOCUMENT["DISCORD"]["WHITELIST_IDS"]
DISCORD_LOG_WEBHOOKS = CONFIG_DOCUMENT["DISCORD"]["LOG_WEBHOOKS"]


NAEU = CONFIG_DOCUMENT["HON"]["NAEU"]
ACP = NAEU["ACP"]

HON_ACP_PROXY_URL = os.getenv("HON_ACP_PROXY_URL")
HON_ACP_AC_DOMAIN = NAEU["AC"]["ACP"]
HON_ACP_RC_DOMAIN = NAEU["RC"]["ACP"]
HON_ACP_TC_DOMAIN = NAEU["TC"]["ACP"]
HON_ACP_USER = os.getenv("HON_ACP_USER")
HON_ACP_PASSWORD = os.getenv("HON_ACP_PASSWORD")
HON_ACP_MAGIC = {"username": HON_ACP_USER, "password": HON_ACP_PASSWORD}
HON_ACP_AUTH = ACP["AUTH"]
HON_ACP_DEAUTH = ACP["DEAUTH"]
HON_ACP_CLAN_SEARCH = ACP["CLAN_SEARCH"]
HON_ACP_CLAN = ACP["CLAN"]
HON_ACP_PROFILE_SEARCH = ACP["PROFILE_SEARCH"]
HON_ACP_PROFILE = ACP["PROFILE"]
HON_ACP_SUSPENSION = ACP["SUSPENSION"]

HON_TYPE_MAP = NAEU["TYPE_MAP"]
HON_STANDING_MAP = NAEU["STANDING_MAP"]


SENTRY = os.getenv("SENTRY", None)


# Database and collections. Please create these in advance in MongoDB.
MONGO_DATABASE_NAME = "rct"
# This collection must index player names using a custom collation with Locale set to en - English and a Strength of 1.
MONGO_TESTING_PLAYERS_COLLECTION_NAME = "testers"
MONGO_TESTING_GAMES_COLLECTION_NAME = "testing_games"
MONGO_TESTING_CYCLES_COLLECTION_NAME = "testing_cycles"
MONGO_TESTING_BUGS_COLLECTION_NAME = "testing_bugs"
MONGO_TESTING_EXTRA_COLLECTION_NAME = "testing_extra"


# TODO: Auto search for uploaded emojis in shared servers.
EMOJI_HON = "<:HoN:742025245564600330>"
EMOJI_RCT = "<:RCT:717710063657156688>"
EMOJI_YAY = "<:yay:717806806889660416>"
EMOJI_NAY = "<:nay:717806831916810251>"
EMOJI_GOLD_COINS = "<:gold:711938379587125340>"
EMOJI_UNRANKED_RANK = "<:Norank:711744503228399616>"
EMOJI_UNRANKED_CHEST = "<:UnrankedChest:711926778524074054>"
EMOJI_BRONZE_RANK = "<:Bronze:711744364367577158>"
EMOJI_BRONZE_CHEST = "<:BronzeChest:711926778339262507>"
EMOJI_SILVER_RANK = "<:Silver:711744335846047744>"
EMOJI_SILVER_CHEST = "<:SilverChest:711926778238861365>"
EMOJI_GOLD_RANK = "<:Gold:711744184478072853>"
EMOJI_GOLD_CHEST = "<:GoldChest:711926778654097458>"
EMOJI_DIAMOND_RANK = "<:Diamond:711744217654886480>"
EMOJI_DIAMOND_CHEST = "<:DiamondChest:711926778368884739>"
EMOJI_LEGENDARY_RANK = "<:Legendary:711744131772186714>"
EMOJI_LEGENDARY_CHEST = "<:LegendaryChest:711926778477936682>"
EMOJI_IMMORTAL_RANK = "<:Immortal:711744275339018323>"
EMOJI_IMMORTAL_CHEST = "<:ImmortalChest:711926778540589126>"
EMOJI_GITHUB = "<:GitHub:725437431188291674>"

# TODO: Clean up.
EXTENSIONS_DIRECTORIES = ["rctbot.core", "rctbot.hon", "rctbot.extensions"]
STARTUP_EXTENSIONS = []
if config.release_stage == "dev":
    DISABLED_EXTENSIONS = ["__init__", "__pycache__", "bot", "spreadsheet", "rolesync", "paginator"]
else:
    DISABLED_EXTENSIONS = ["__init__", "__pycache__", "bot"]
LOADED_EXTENSIONS = []


CONFIG_FILE = __loader__.name
DATABASE_READY = False
LAST_RETRIEVED = None
LIST_OF_LISTS = []
LIST_OF_LISTS_TRIVIA = []
PLAYER_SLASH_HERO = []
SETTINGS = []
