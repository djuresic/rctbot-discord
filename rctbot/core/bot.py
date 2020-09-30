"""
RCTBot A simple Discord bot with some Heroes of Newerth integration.
Copyright (C) 2020  Danijel Jurešić

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

import discord
from discord.ext import commands

import rctbot.config

# TODO: Custom help. help_command

# NOTE: commands.when_mentioned_or(*prefixes) returns another callable. If done
# inside a custom callable, the returned callable must be called. Follow
# get_prefix(bot, message) example from docstring.


class RCTBot(commands.Bot):
    """The one and only RCTBot.
    
    This class is inherited from discord.ext.commands.Bot"""

    def __init__(self, *, version: str):
        self.version = version
        self.platform = platform.platform()
        super().__init__(
            command_prefix=commands.when_mentioned_or(*[".", "!"]),
            case_insensitive=True,
            intents=discord.Intents.all(),
        )
        self._load_extensions()
        self._remove_help()

    def _load_extensions(self):
        for extension_directory in rctbot.config.EXTENSIONS_DIRECTORIES:
            # TODO: Refactor this.
            with os.scandir(extension_directory.replace(".", "/")) as it:
                for entry in it:
                    if entry.name.endswith(".py") and entry.is_file():
                        bot_module = entry.name[:-3]
                        if bot_module not in rctbot.config.DISABLED_EXTENSIONS:
                            rctbot.config.STARTUP_EXTENSIONS.append(f"{extension_directory}.{bot_module}")

        for bot_extension in rctbot.config.STARTUP_EXTENSIONS:
            try:
                self.load_extension(bot_extension)
            except Exception as e:
                exc = "{}: {}".format(type(e).__name__, e)
                print(f"Failed to load {bot_extension}\n{exc}")

        print(
            "Loaded modules: {}".format(
                ", ".join([bot_extension.split(".")[-1] for bot_extension in rctbot.config.LOADED_EXTENSIONS])
            )
        )

    # Remove help until custom help is implemented.
    def _remove_help(self):
        self.remove_command("help")

    def run(self):  # pylint: disable=arguments-differ
        try:
            super().run(rctbot.config.DISCORD_TOKEN)
        except discord.LoginFailure:
            print("Login failure! Re-check the config file and your Discord bot token.")
            raise discord.LoginFailure

    async def close(self):
        return await super().close()
