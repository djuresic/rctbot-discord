import asyncio
from datetime import datetime, timezone

from discord.ext import tasks, commands

import gspread
import gspread_asyncio
from gspread_asyncio import _nowait
from oauth2client.service_account import ServiceAccountCredentials

import config
from extensions.checks import is_senior


# gspread_asyncio doesn't currently include changes made to some methods in gspread, overriding:
class AsyncioGspreadClientManagerUpdated(gspread_asyncio.AsyncioGspreadClientManager):
    async def _authorize(self):
        now = self._loop.time()
        if self.auth_time == None or self.auth_time + self.reauth_interval < now:
            creds = await self._loop.run_in_executor(None, self.credentials_fn)
            gc = await self._loop.run_in_executor(None, gspread.authorize, creds)
            agc = AsyncioGspreadClientUpdated(self, gc)
            self._agc_cache[now] = agc
            if self.auth_time in self._agc_cache:
                del self._agc_cache[self.auth_time]
            self.auth_time = now
        else:
            agc = self._agc_cache[self.auth_time]
        return agc


class AsyncioGspreadClientUpdated(gspread_asyncio.AsyncioGspreadClient):
    async def open(self, title):
        """Opens a Google Spreadsheet by title. Wraps :meth:`gspread.Client.open`.
        Feel free to call this method often, even in a loop, as it caches the underlying spreadsheet object.
        :param title: The title of the spreadsheet
        :type title: str
        :returns: :class:`~gspread_asyncio.AsyncioGspreadSpreadsheet`
        """
        if title in self._ss_cache_title:
            return self._ss_cache_title[title]
        ss = await self.agcm._call(self.gc.open, title)
        ass = AsyncioGspreadSpreadsheetUpdated(self.agcm, ss)
        self._ss_cache_title[title] = ass
        self._ss_cache_key[ss.id] = ass
        return ass


class AsyncioGspreadSpreadsheetUpdated(gspread_asyncio.AsyncioGspreadSpreadsheet):
    async def worksheet(self, title):
        """Gets a worksheet (tab) by title. Wraps :meth:`gspread.models.Spreadsheet.worksheet`.
        Feel free to call this method often, even in a loop, as it caches the underlying worksheet object.
        :param title: Human-readable title of the worksheet.
        :type title: str
        :returns: :class:`~gspread_asyncio.AsyncioGspreadWorksheet`
        """
        if title in self._ws_cache_title:
            return self._ws_cache_title[title]
        ws = await self.agcm._call(self.ss.worksheet, title)
        aws = AsyncioGspreadWorksheetUpdated(self.agcm, ws)
        self._ws_cache_title[title] = aws
        self._ws_cache_idx[ws._properties["index"]] = aws
        return aws


class AsyncioGspreadWorksheetUpdated(gspread_asyncio.AsyncioGspreadWorksheet):
    @_nowait
    async def append_row(
        self,
        values,
        value_input_option="RAW",
        insert_data_option=None,  # Not in gspread_asyncio.
        table_range=None,  # Not in gspread_asyncio.
    ):  # https://github.com/burnash/gspread/issues/537
        """Adds a row to the worksheet and populates it with values. Widens the worksheet if there are more values than columns. Wraps :meth:`gspread.models.Worksheet.append_row`.
        :param values: List of values for the new row.
        :param value_render_option: (optional) Determines how values should be
                                    rendered in the the output. See
                                    `ValueRenderOption`_ in the Sheets API.
        :type insert_data_option: str
        :param table_range: (optional) The A1 notation of a range to search for
                             a logical table of data. Values are appended after
                             the last row of the table.
                             Examples: `A1` or `B2:D4`
        :type table_range: str
        .. _ValueInputOption: https://developers.google.com/sheets/api/reference/rest/v4/ValueInputOption
        .. _InsertDataOption: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append#InsertDataOption
        """
        return await self.agcm._call(
            self.ws.append_row,
            values,
            value_input_option=value_input_option,
            insert_data_option=insert_data_option,
            table_range=table_range,
        )


def get_creds():
    """Returns Service Account credentials."""
    return ServiceAccountCredentials.from_json_keyfile_name(
        config.GOOGLE_CLIENT_SECRET_FILE, config.GOOGLE_SCOPES
    )


# Do spreadsheet.client() instead of spreadsheet.CLIENT_MANAGER.authorize()

# CLIENT_MANAGER = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
CLIENT_MANAGER = AsyncioGspreadClientManagerUpdated(get_creds)


async def set_client():
    """Calls authorize() method on client manager and returns a ready-to-use client."""
    return await CLIENT_MANAGER.authorize()


class Spreadsheet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counter = 0
        self.fetch.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.fetch.cancel()  # pylint: disable=no-member

    @tasks.loop(seconds=65.0)
    async def fetch(self):
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
        config.LAST_RETRIEVED = datetime.now(timezone.utc)

        self.counter += 1

    @fetch.before_loop
    async def before_fetch(self):
        print("Synchronizing with Google Sheets.")

    @fetch.after_loop
    async def after_fetch(self):
        print("No longer synchronizing with Google Sheets.")

    @commands.group(hidden=True)
    @is_senior()
    async def spreadsheet(self, ctx):
        pass

    @spreadsheet.command(name="counter")
    async def _counter(self, ctx):
        await ctx.send(f"Times successful: {self.counter}")


def setup(bot):
    bot.add_cog(Spreadsheet(bot))
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
