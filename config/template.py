# NOTE: If a variable does not have a comment with a description, the name is most likely self explanatory.

# ----------------------------------------------- Discord Configuration ---------------------------------------------- #

# Discord bot token, obtained from within your application. https://discord.com/developers/applications
DISCORD_TOKEN = ""
# Channel where testing notes log will be sent.
DISCORD_NOTES_CHANNEL_ID = 0
# Channel ID of your announcements channel.
DISCORD_ANNOUNCEMENTS_CHANNEL_ID = 0
# Role ID of the Forums role. Mentioning this role on announcements channel will forward text followed by it to
# the Announcements thread in the RCT sub forum. TODO: Create this role automatically if it doesn't exist.
DISCORD_FORUMS_ROLE_ID = 0
# Channel ID for channel where bug reports will be sent.
DISCORD_BUGS_CHANNEL_ID = 0
# General bot log channel ID.
DISCORD_BOT_LOG_CHANNEL_ID = 0
# Game lobbies channel ID.
DISCORD_GAME_LOBBIES_CHANNEL_ID = 0
# Watchdog channel ID.
DISCORD_WATCHDOG_CHANNEL_ID = 0
# Welcome channel ID. This is usually the #general channel.
DISCORD_WELCOME_CHANNEL_ID = 0
# Allowlist (or blocklist, depending on how you use it) for user IDs. It can be used to restrict certain commands.
DISCORD_WHITELIST_IDS = []
# List of Discord webhook URLs for bot log.
DISCORD_LOG_WEBHOOKS = []
# List of commands allowed in DM. TODO: This has to go. Replace with a decorator.
DISCORD_DM_COMMANDS = []

# ----------------------------------------------- Discord Emoji Strings ---------------------------------------------- #

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


# ------------------------------------------ Heroes of Newerth Configuration ----------------------------------------- #

# TODO: Remove, streamline and use custom UA.
HON_GAME_CLIENT = "S2 Games/Heroes of Newerth"
# HoN user agent string.
HON_USER_AGENT = "S2 Games/Heroes of Newerth/4.8.4.1/lac/x86-biarch"
# Client version to use in AC user agent.
HON_UA_VERSION = "4.8.4.1"
# Client version to use in RC user agent.
HON_UA_RC_VERSION = "0.0.0"
# Client version to use in TC user agent.
HON_UA_TC_VERSION = "0.0.0"

# HoN International (NAEU) authentication server hostname.
HON_NAEU_AC_MASTERSERVER = ""
# HoN International (NAEU) RC and TC authentication servers' hostnames.
HON_NAEU_RC_MASTERSERVER = ""
HON_NAEU_TC_MASTERSERVER = ""

# String of characters after dash in os query parameter for RC and TC. These are requires for client version checking
# and other interaction with test clients' authentication servers. In order to know these, you must have access to their
# respective clients. If you don't, ask RCT and SBT staff for assistance.
HON_NAEU_RC_OS_PART = ""
HON_NAEU_TC_OS_PART = ""

# Sefe prime N and generator g crypto parameters for SRP authentication.
HON_S2_N = "DA950C6C97918CAE89E4F5ECB32461032A217D740064BC12FC0723CD204BD02A7AE29B53F3310C13BA998B7910F8B6A14112CBC67BDD2427EDF494CB8BCA68510C0AAEE5346BD320845981546873069B337C073B9A9369D500873D647D261CCED571826E54C6089E7D5085DC2AF01FD861AE44C8E64BCA3EA4DCE942C5F5B89E5496C2741A9E7E9F509C261D104D11DD4494577038B33016E28D118AE4FD2E85D9C3557A2346FAECED3EDBE0F4D694411686BA6E65FEE43A772DC84D394ADAE5A14AF33817351D29DE074740AA263187AB18E3A25665EACAA8267C16CDE064B1D5AF0588893C89C1556D6AEF644A3BA6BA3F7DEC2F3D6FDC30AE43FBD6D144BB"
HON_S2_G = "2"

# The official HoN authentication server uses these in SRP, but they may not be accissible to you. If you are setting up
# an official instance of RCTBot, please contact a system administrator or a server engineer. Leave these emtpy if you
# do not need masterserver queries or if you use other similar APIs. This also serves as a check for the masterserver
# module as leaving these empty will disable it. NOTE: This check has not been implemented yet!
HON_SRP_SS = ""
HON_SRP_SL = ""

# Patch notes generator domain.
HON_ALT_DOMAIN = ""
# Patch notes access token creation password.
HON_CAT_PASSWORD = ""

# NOTE: HoN forums related variables below are currently not in use.

# Bot forum username.
HON_FORUM_USER = ""
# Bot forum password.
HON_FORUM_USER_PASSWORD = ""
# Bot forum account ID.
HON_FORUM_USER_ACCOUNT_ID = ""
# RCT announcements forum thread ID.
HON_FORUM_ANNOUNCEMENTS_THREAD_ID = ""
# RCT bugs subforum ID.
HON_FORUM_RCT_BUGS_SUBFORUM_ID = ""
# Boolean indication whether or not to create all bug report threads (including Art & Sound, HoN Store, etc.)
HON_FORUM_CREATE_ALL_THREADS = False
# Limit the number of screenshots allowed in bug reports to this number.
HON_FORUM_SCREENSHOT_LIMIT = 6

# NOTE: ACP is intended for staff only. If you are Frostburn staff, please assign correct values to the variables below.

# Proxy URL for ACP proxy.
HON_ACP_PROXY_URL = ""
# International (NA/EU) ACP domain.
HON_ACP_AC_DOMAIN = ""
# International (NA/EU) RC ACP domain.
HON_ACP_RC_DOMAIN = ""
# International (NA/EU) TC ACP domain.
HON_ACP_TC_DOMAIN = ""
# Username of the ACP user, case sensitive.
HON_ACP_USER = ""
# Dictionary containing POST data sent during ACP user authentiation.
HON_ACP_MAGIC = {}
# ACP authentication path. Must start with a forward slash (/).
HON_ACP_AUTH = ""
HON_ACP_DEAUTH = ""  # TODO
# ACP clan paths. Must start with a forward slash (/).
HON_ACP_CLAN_SEARCH = ""
HON_ACP_CLAN = ""
# ACP profile paths. Must start with a forward slash (/).
HON_ACP_PROFILE_SEARCH = ""
HON_ACP_PROFILE = ""
# ACP suspension check path. Must start with a forward slash (/).
HON_ACP_SUSPENSION = ""

# HoN Volunteer Portal base URL.
HON_VP_URL = ""

# Username and password for HoN NA/EU AC bot account.
HON_USERNAME = ""
HON_PASSWORD = ""

# Username and password for HoN NA/EU RC bot account.
HON_RC_USERNAME = ""
HON_RC_PASSWORD = ""

# Username and password for HoN NA/EU TC bot account.
HON_TC_USERNAME = ""
HON_TC_PASSWORD = ""

# TODO: Separate file.
# These you must translate yourself.
HON_TYPE_MAP = {
    "0": "Type 0",
    "1": "Type 1",
    "2": "Type 2",
    "3": "Type 3",
    "4": "Type 4",
    "5": "Type 5",
    "6": "Type 6",
    "7": "Type 7",
    "8": "Type 8",
    "9": "Type 9",
    "10": "Type 10",
    "11": "Type 11",
}
# TODO: Separate file.
HON_STANDING_MAP = {"0": "None", "1": "Basic", "2": "Verified", "3": "Legacy"}

# List of offensive words. Used by the Watchdog module. TODO: Separate file.
HON_WORD_LIST = []

# ----------------------------------------------- MongoDB Configuration ---------------------------------------------- #

# This is passed as the host parameter. It can be a simple hostname, a MongoDB URI, or a list of hostnames or URIs.
# Ensure that any option parameters are URL encoded. NOTE: from urllib.parse import quote_plus
# NOTE: For MongoDB Atlas Cloud, database name variable must have the same database name from the connection URI.
# localhost:27017 is the default host parameter.
MONGO_HOST_PARAMETER = ""

# Database and collections. Please create these in advance in MongoDB.
MONGO_DATABASE_NAME = ""
# This collection must index player names using a custom collation with Locale set to en - English and a Strength of 1.
MONGO_TESTING_PLAYERS_COLLECTION_NAME = ""
MONGO_TESTING_GAMES_COLLECTION_NAME = ""
MONGO_TESTING_CYCLES_COLLECTION_NAME = ""
MONGO_TESTING_BUGS_COLLECTION_NAME = ""


# Required for Google Spreadsheets only. Disable spreadsheet module if not in use.
GOOGLE_CLIENT_SECRET_FILE = "your_file.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://spreadsheets.google.com/feeds",
]


# ------------------------------------------- Web Application Configuration ------------------------------------------ #

# Mostly for interaction with pyHoNBot.
WEB_LOCAL_IP = "localhost"
WEB_LOCAL_PORT = 8080
WEB_DOMAIN = "localhost:8080"
WEB_TOKEN = "thisiswherethetokenslashpasswordgoes"
WEB_GAME_LOBBY_PATH = "/some/path/to/lobby"
WEB_CHAT_COLOR_PATH = "/some/path/to/chat/color"


# ------------------------------------------- Bot Extensions Configuration ------------------------------------------- #

EXTENSIONS_DIRECTORIES = ["core", "hon", "extensions"]
STARTUP_EXTENSIONS = []
DISABLED_EXTENSIONS = ["__init__"]
LOADED_EXTENSIONS = []


# ----------------------------------------- Dynamic Variables - DO NOT TOUCH! ---------------------------------------- #
# TODO: Remove old spreadsheet stuff.
CONFIG_FILE = __loader__.name
DATABASE_READY = False
LAST_RETRIEVED = None
LIST_OF_LISTS = []
LIST_OF_LISTS_TRIVIA = []
PLAYER_SLASH_HERO = []
SETTINGS = []

print(f"Loaded {CONFIG_FILE}")
