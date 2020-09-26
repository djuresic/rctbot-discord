from __future__ import annotations

import os
import asyncio
from typing import Tuple, Union

import aiohttp
from bs4 import BeautifulSoup


import rctbot.config

HON_VP_USER = os.getenv("HON_VP_USER", "RCTBot")
HON_VP_PASSWORD = os.getenv("HON_VP_PASSWORD", None)


# FIXME: Not singleton pattern.
class VPClient:
    """Class representing a HoN Volunteer Portal client.
    
    Asynchronous context manager if `async with` statement is used.
    Creates a new session if one isn't provided."""

    def __init__(self, session=None) -> None:
        self.url = "https://volunteers.heroesofnewerth.com"
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.token = None

    async def __aenter__(self) -> VPClient:
        await self.authenticate()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def close(self) -> None:
        """Coroutine. Log out and close the session."""
        await self.request("/auth/logout", method="GET")
        await self.session.close()

    async def authenticate(self) -> bool:
        """Coroutine. Perform authentication. Returns authenticated status as bool."""
        status, text = await self.request("/auth", method="GET")
        if status != 200:
            return False

        def find_token(response_text) -> str:
            soup = BeautifulSoup(response_text, "lxml")
            return soup.find(attrs={"name": "_token"})["value"]

        loop = asyncio.get_running_loop()
        self.token = await loop.run_in_executor(None, find_token, text)

        data = {
            "_token": self.token,
            "password": HON_VP_PASSWORD,
            "username": HON_VP_USER,
        }

        status, text = await self.request("/auth/login", data=data)
        return bool(status == 200 and HON_VP_USER in text)

    async def request(
        self, path, params=None, data=None, method="POST", chunked=None, read_until_eof=True,
    ) -> Tuple[int, str]:
        """Coroutine. Ensure the client is authenticated and perform a HTTP request.
        
        Return tuple (status, text) from HTTP response."""

        status, text = await self._do_request(path, params, data, method, chunked, read_until_eof)
        if status in [401, 403, 500]:
            for attempt in range(5):
                authenticated = await self.authenticate()
                if authenticated:
                    status, text = await self._do_request(path, params, data, method, chunked, read_until_eof)
                    return status, text
                else:
                    print(f"Portal authentication attempt {attempt+1} failed")
                await asyncio.sleep(attempt + 2)
            return status, text
        else:
            return status, text

    async def _do_request(self, path, params, data, method, chunked, read_until_eof) -> Tuple[int, str]:
        async with self.session.request(
            method=method,
            url=f"{self.url}{path}",
            params=params,
            data=data,
            chunked=chunked,
            read_until_eof=read_until_eof,
        ) as response:
            return response.status, (await response.text())

    async def get_tokens(self, account_id) -> float:
        """Coroutine. Get tokens value for account ID."""
        path = f"/admin/user/edit/o/5/u/{account_id}"
        status, text = await self.request(path, method="GET")
        if status == 200:

            def find_tokens_value(response_text) -> float:
                soup = BeautifulSoup(response_text, "lxml")
                return float(soup.find(attrs={"name": "tokens"})["value"])

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, find_tokens_value, text)

        return 0.0

    async def mod_tokens(self, mod_input) -> Tuple[Union[None, str], Union[None, str]]:
        """Coroutine. Perform modify tokens action.

        Input can be a sigle string with a username, followed by how many tokens to take orgive, or a list of those
        strings. e.g. Give Lightwalker 100 tokens and remove 50: ["Lightwalker 100", "Lightwalker -50"]"""
        path = "/admin/tokens/mod/o/5"
        if isinstance(mod_input, list):
            input_list = mod_input
        else:
            input_list = [mod_input]
        data = {
            "_token": self.token,
            "modInput": "\n".join(input_list),
        }
        status, text = await self.request(path, data=data)

        def mod_tokens_result(response_text) -> Tuple[Union[None, str], Union[None, str]]:
            soup = BeautifulSoup(response_text, "lxml")
            success = soup.find(attrs={"class": "alert-success"})
            error = soup.find(attrs={"class": "alert-danger"})
            # TODO: Extract list items in case of error.
            if success is not None:
                success = success.string
            if error is not None:
                error = error.string
            return success, error

        if status == 200:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, mod_tokens_result, text)

        return (
            None,
            f"Failed to modify tokens. Status code: {status}",
        )


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
