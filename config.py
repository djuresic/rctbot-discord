import os
import platform
import json

# Heroku
if "DYNO" in os.environ:
    HEROKU_DEPLOYED = True
else:
    HEROKU_DEPLOYED = False

# Load local config, platform for dev purposes
if "Windows" in platform.system():
    CONFIG_FILE = "dev_config.json"
else:
    CONFIG_FILE = "config.json"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as CONFIG:
        CONFIG = json.load(CONFIG)
        try:
            CONFIG_DISCORD = CONFIG["DISCORD"]
            CONFIG_HON = CONFIG["HON"]
            CONFIG_GOOGLE = CONFIG["GOOGLE"]
            CONFIG_WEB = CONFIG["WEB"]

            if HEROKU_DEPLOYED:
                CONFIG_HEROKU = CONFIG["HEROKU"]
                HEROKU_APP_NAME = CONFIG_HEROKU[
                    "APP_NAME"
                ]  # TO DO: finish this and clean up
        except:
            raise Exception("Invalid configuration file or missing keys.")
else:
    raise Exception(f"Missing configuration file {CONFIG_FILE} in directory.")

# Extensions
BOT_EXTENSIONS_DIRECTORY = "extensions"
BOT_STARTUP_EXTENSIONS = []
BOT_DISABLED_EXTENSIONS = []
BOT_LOADED_EXTENSIONS = []

# Discord
DISCORD_TOKEN = CONFIG_DISCORD["TOKEN"]
DISCORD_NOTES_CHANNEL_ID = CONFIG_DISCORD["NOTES_CHANNEL_ID"]
DISCORD_ANNOUNCEMENTS_CHANNEL_ID = CONFIG_DISCORD["ANNOUNCEMENTS_CHANNEL_ID"]
DISCORD_FORUMS_ROLE_ID = CONFIG_DISCORD["FORUMS_ROLE_ID"]
DISCORD_BUGS_CHANNEL_ID = CONFIG_DISCORD["BUGS_CHANNEL_ID"]
DISCORD_BOT_LOG_CHANNEL_ID = CONFIG_DISCORD["BOT_LOG_CHANNEL_ID"]
DISCORD_GAME_LOBBIES_CHANNEL_ID = CONFIG_DISCORD["GAME_LOBBIES_CHANNEL_ID"]
DISCORD_WHITELIST_IDS = CONFIG_DISCORD["WHITELIST_IDS"]

DISCORD_DM_COMMANDS = [
    "report",
    "notes",
]  # TO DO: replace with a decorator (guild_only and dm_allowed)


# Heroes of Newerth
HON_GAME_CLIENT = CONFIG_HON["GAME_CLIENT"]
HON_USER_AGENT = CONFIG_HON["USER_AGENT"]
HON_UA_VERSION = CONFIG_HON["UA_VERSION"]
HON_UA_RC_VERSION = CONFIG_HON["UA_RC_VERSION"]
HON_UA_TC_VERSION = CONFIG_HON["UA_TC_VERSION"]
HON_NAEU_MASTERSERVER = CONFIG_HON["NAEU_MASTERSERVER"]
HON_NAEU_RC_MASTERSERVER = CONFIG_HON["NAEU_RC_MASTERSERVER"]
HON_NAEU_TC_MASTERSERVER = CONFIG_HON["NAEU_TC_MASTERSERVER"]
HON_NAEU_RC_OS_PART = CONFIG_HON["NAEU_RC_OS_PART"]
HON_NAEU_TC_OS_PART = CONFIG_HON["NAEU_TC_OS_PART"]
HON_REGION = CONFIG_HON["REGION"]
HON_S2_N = CONFIG_HON["S2_N"]
HON_S2_G = CONFIG_HON["S2_G"]
HON_SRP_SS = CONFIG_HON["SRP_SS"]
HON_SRP_SL = CONFIG_HON["SRP_SL"]
HON_ALT_DOMAIN = CONFIG_HON["ALT_DOMAIN"]
HON_CAT_PASSWORD = CONFIG_HON["CAT_PASSWORD"]
HON_FORUM_USER = CONFIG_HON["FORUM_USER"]
HON_FORUM_USER_MD5_PASSWORD = CONFIG_HON["FORUM_USER_MD5_PASSWORD"]
HON_FORUM_USER_ACCOUNT_ID = CONFIG_HON["FORUM_USER_ACCOUNT_ID"]
HON_FORUM_ANNOUNCEMENTS_THREAD_ID = CONFIG_HON["FORUM_ANNOUNCEMENTS_THREAD_ID"]
HON_FORUM_RCT_BUGS_SUBFORUM_ID = CONFIG_HON["FORUM_RCT_BUGS_SUBFORUM_ID"]
HON_FORUM_CREATE_ALL_THREADS = CONFIG_HON["FORUM_CREATE_ALL_THREADS"]
HON_FORUM_SCREENSHOT_LIMIT = CONFIG_HON["FORUM_SCREENSHOT_LIMIT"]

HON_TYPE_MAP = CONFIG_HON["TYPE_MAP"]
HON_STANDING_MAP = CONFIG_HON["STANDING_MAP"]

HON_TC_PASSWORD = CONFIG_HON["TC_PASSWORD"]
HON_TC_USERNAME = CONFIG_HON["TC_USERNAME"]

HON_RC_PASSWORD = CONFIG_HON["RC_PASSWORD"]
HON_RC_USERNAME = CONFIG_HON["RC_USERNAME"]

HON_PASSWORD = CONFIG_HON["PASSWORD"]
HON_USERNAME = CONFIG_HON["USERNAME"]

# Let's try this
HON_MASTERSERVER_INFO = {
    "ac": {
        "short": "Retail",
        "hostname": HON_NAEU_MASTERSERVER,
        "client": "Heroes of Newerth",
        "version": HON_UA_VERSION,
        "user": HON_USERNAME,
        "password": HON_PASSWORD,
        "authenticated": False,
        "nickname": "",
        "account_id": 0,
        "cookie": "",
        "ip": "",
        "auth_hash": "",
        "chat_url": "",
        "chat_port": 0,
        "thing": "",
    },
    "rc": {
        "short": "RCT",
        "hostname": HON_NAEU_RC_MASTERSERVER,
        "client": "Heroes of Newerth Release Candidate",
        "version": HON_UA_RC_VERSION,
        "user": HON_RC_USERNAME,
        "password": HON_RC_PASSWORD,
        "authenticated": False,
        "nickname": "",
        "account_id": 0,
        "cookie": "",
        "ip": "",
        "auth_hash": "",
        "chat_url": "",
        "chat_port": 0,
        "thing": "",
    },
    "tc": {
        "short": "SBT",
        "hostname": HON_NAEU_TC_MASTERSERVER,
        "client": "Heroes of Newerth Private Test",
        "version": HON_UA_TC_VERSION,
        "user": HON_TC_USERNAME,
        "password": HON_TC_PASSWORD,
        "authenticated": False,
        "nickname": "",
        "account_id": 0,
        "cookie": "",
        "ip": "",
        "auth_hash": "",
        "chat_url": "",
        "chat_port": 0,
        "thing": "",
    },
}


# Google
GOOGLE_CLIENT_SECRET_FILE = CONFIG_GOOGLE["CLIENT_SECRET_FILE"]
GOOGLE_SCOPES = CONFIG_GOOGLE["SCOPES"]


# Web
WEB_LOCAL_IP = CONFIG_WEB["LOCAL_IP"]
WEB_LOCAL_PORT = CONFIG_WEB["LOCAL_PORT"]
WEB_DOMAIN = CONFIG_WEB["DOMAIN"]
WEB_TOKEN = CONFIG_WEB["TOKEN"]
WEB_GAME_LOBBY_PATH = CONFIG_WEB["GAME_LOBBY_PATH"]


# dynamic
DATABASE_READY = False
SYNC_SPREADSHEET = False
LIST_OF_LISTS = []
LIST_OF_LISTS_TRIVIA = []
PLAYER_SLASH_HERO = []
SETTINGS = []

print("Loaded configuration.")
