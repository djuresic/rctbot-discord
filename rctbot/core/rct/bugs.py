from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler

# Move to models?
@dataclass
class BugReport:
    """
    Bug report model.
    """

    reporter: dict
    category: str = None
    description: str = None
    version: str = None
    build_date: str = None
    created_at: datetime = datetime.now(timezone.utc)
    # created_at: datetime = field(default_factory=datetime.now(timezone.utc))


class BugReportManagerResult:
    pass


class BugReportManager:
    """
    Interface for managing RCT bug reports. Not an asynchronous context manager.
    """

    def __init__(self):
        # Database
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_bugs = self.db[rctbot.config.MONGO_TESTING_BUGS_COLLECTION_NAME]

    async def insert(self, report: BugReport):
        """Insert a bug report.

        Args:
            report (BugReport): Bug report to insert.

        Returns:
            str: Result message.
        """
        result = await self.testing_bugs.insert_one(
            {
                "reporter": report.reporter,
                "category": report.category,
                "description": report.description,
                "version": report.version,
                "build_date": report.build_date,
                "created_at": report.created_at,
            }
        )
        # TODO: BugReportManagerResult
        if result.acknowledged:
            return f'Inserted report for {report.reporter["nickname"]}.'
        return f'Could not insert report for {report.reporter["nickname"]}.'
