from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler

# Move to models?
@dataclass
class ExtraTokens:
    """
    Extra tokens model.
    """

    tester: dict
    amount: int
    reason: str = None
    created_at: datetime = datetime.now(timezone.utc)  # FIXME: something's wrong, need to read the docs
    # created_at: datetime = field(default_factory=datetime.now(timezone.utc))


class ExtraTokensManagerResult:
    pass


class ExtraTokensManager:
    """
    Interface for managing extra tokens. Not an asynchronous context manager.
    """

    def __init__(self):
        # Database
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]
        self.testing_extra = self.db[rctbot.config.MONGO_TESTING_EXTRA_COLLECTION_NAME]

    async def insert(self, extra: ExtraTokens):
        """Insert extra tokens.

        Args:
            extra (ExtraTokens): Extra tokens to insert.

        Returns:
            str: Result message.
        """
        result = await self.testing_extra.insert_one(
            {"tester": extra.tester, "amount": extra.amount, "reason": extra.reason, "created_at": extra.created_at}
        )
        # TODO: ExtraTokensManagerResult
        if result.acknowledged:
            return f'Added {extra.amount} extra tokens to {extra.tester["nickname"]}.'
        return f'Could not add {extra.amount} extra tokens to {extra.tester["nickname"]}.'
