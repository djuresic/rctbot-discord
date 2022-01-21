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

from rctbot.core.rct.bugs import BugReport, BugReportManager
from rctbot.core.rct.cycle import CycleValues, CycleManager, CycleManagerResult
from rctbot.core.rct.extra import ExtraTokens, ExtraTokensManager
from rctbot.core.rct.match import MatchManipulator
from rctbot.core.rct.models import ActivityRank, Perks, Role
from rctbot.core.rct.notes import TestingNotes
from rctbot.core.rct.tester import TesterManager, TesterManagerResult

# TODO: Inherit from BaseManager, BaseManagerResult?

# from rctbot.core.rct import *
__all__ = [
    "BugReport",
    "BugReportManager",
    "CycleValues",
    "CycleManager",
    "CycleManagerResult",
    "ExtraTokens",
    "ExtraTokensManager",
    "MatchManipulator",
    "ActivityRank",
    "Perks",
    "Role",
    "TestingNotes",
    "TesterManager",
    "TesterManagerResult",
]
