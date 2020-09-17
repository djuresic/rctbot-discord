from typing import Union

import aiohttp

import rctbot.config


class TestingNotes:
    """
    Class representing Testing Notes.
    """

    def __init__(self) -> None:
        self.domain = rctbot.config.HON_ALT_DOMAIN
        self.password = rctbot.config.HON_CAT_PASSWORD

    async def create(self, discord_id: Union[int, str]) -> str:
        """Create a Testing Notes access token for a user.

        Uses an existing one if present.

        Args:
            discord_id (Union[int, str]): Discord user ID of the user.

        Returns:
            str: Testing Notes URL.
        """
        cat = f"https://{self.domain}/site/create-access-token"
        cat_query = {"discordId": discord_id, "password": self.password}

        async with aiohttp.ClientSession() as session:
            async with session.get(cat, params=cat_query) as resp:
                token = await resp.text()

        return f"https://{self.domain}/{token}"

    async def delete(self, discord_id: Union[int, str]) -> bool:
        """Delete an exisiting Testing Notes access token for a user.

        Args:
            discord_id (Union[int, str]): Discord user ID of the user.

        Returns:
            bool: Whether the action was successful. This is False if Testing
                Notes access token has never been created for the user.
        """
        dat = f"https://{self.domain}/site/delete-access-token"
        dat_query = {"discordId": discord_id, "password": self.password}

        async with aiohttp.ClientSession() as session:
            async with session.get(dat, params=dat_query) as resp:
                deleted = bool((await resp.text()) == "1")

        return deleted
