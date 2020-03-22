import asyncio

import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

import config

# This should properly use discord.ext.tasks ASAP; meanwhile it must N E V E R be reloaded!

FETCH_SHEET_PASS = 0


def get_creds():
    """Returns Service Account credentials."""
    return ServiceAccountCredentials.from_json_keyfile_name(
        config.GOOGLE_CLIENT_SECRET_FILE, config.GOOGLE_SCOPES
    )


# Do spreadsheet.client() instead of spreadsheet.CLIENT_MANAGER.authorize()
CLIENT_MANAGER = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


async def set_client():
    """Calls authorize() method on client manager and returns a ready-to-use client."""
    return await CLIENT_MANAGER.authorize()


async def sync_spreadsheet(bot):
    # await bot.wait_until_ready()
    global FETCH_SHEET_PASS

    count_pass = 0
    # while not bot.is_closed:
    while config.SYNC_SPREADSHEET:
        gspread_client = (
            await set_client()
        )  # "This is fine." (It's actually fine, for real. gspread_asyncio has a cache.)

        # Spreadsheet and worksheets
        rct_spreadsheet = await gspread_client.open("RCT Spreadsheet")
        rewards_worksheet = await rct_spreadsheet.worksheet("RCT Players and Rewards")
        trivia_worksheet = await rct_spreadsheet.worksheet("trivia_sheet")
        settings_worksheet = await rct_spreadsheet.worksheet("Settings")
        games_worksheet = await rct_spreadsheet.worksheet("Games")

        # Update dynamic
        config.LIST_OF_LISTS = await rewards_worksheet.get_all_values()
        config.LIST_OF_LISTS_TRIVIA = await trivia_worksheet.get_all_values()
        config.SETTINGS = await settings_worksheet.col_values(2)
        config.PLAYER_SLASH_HERO = await games_worksheet.col_values(13)

        config.DATABASE_READY = True

        count_pass += 1
        FETCH_SHEET_PASS = count_pass
        if count_pass <= 2:
            print("fetch_sheet pass {0}".format(FETCH_SHEET_PASS))

        await asyncio.sleep(60)
    print("Some instance of sync_spreadsheet stopped. :)")  # :(


def setup(bot):
    config.SYNC_SPREADSHEET = True
    # Yes, I just did it so you don't have to. D O  N O T  D O  T H I S!
    bot.loop.create_task(sync_spreadsheet(bot))
    print("Synchronizing with Google Sheets.")
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.SYNC_SPREADSHEET = False  # Just... don't.
    print(
        "No longer synchronizing with Google Sheets."
    )  # Doesn't cancel the task, yep...
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
