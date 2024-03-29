"""
RCTBot A Discord bot with Heroes of Newerth integration.
Copyright (C) 2020–2022  Danijel Jurešić

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

__version__ = "0.0.5"


from rctbot.core.bot import RCTBot


def get_bot():
    return RCTBot(version=__version__)
