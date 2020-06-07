import aiohttp
import asyncio
from bs4 import BeautifulSoup

import core.perseverance
import core.config as config


# FIXME: Not singleton pattern.
class VPClient:
    def __init__(self, session=None):
        self.url = config.HON_VP_URL
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.token = None

    # async def __aenter__(self) -> "VPClient":
    async def __aenter__(self):
        await self.authenticate()
        return self

    # async def __aexit__(self, *_) -> None:
    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        await self.session.close()

    async def authenticate(self):
        status, text = await self.request("/auth", method="GET")
        if status != 200:
            return False

        def find_token(response_text):
            soup = BeautifulSoup(response_text, "lxml")
            return soup.find(attrs={"name": "_token"})["value"]

        loop = asyncio.get_running_loop()
        self.token = await loop.run_in_executor(None, find_token, text)

        data = {
            "_token": self.token,
            "password": config.HON_FORUM_USER_PASSWORD,
            "username": config.HON_FORUM_USER,
        }

        status, text = await self.request("/auth/login", data=data)
        if status == 200 and config.HON_FORUM_USER in text:
            return True
        else:
            return False

    async def request(
        self,
        path,
        params=None,
        data=None,
        method="POST",
        chunked=None,
        read_until_eof=True,
    ):

        status, text = await self._do_request(
            path, params, data, method, chunked, read_until_eof
        )
        if status in [401, 403, 500]:
            for attempt in range(5):
                authenticated = await self.authenticate()
                if authenticated:
                    status, text = await self._do_request(
                        path, params, data, method, chunked, read_until_eof
                    )
                    return status, text
                else:
                    print(f"Portal authentication attempt {attempt+1} failed")
                await asyncio.sleep(attempt + 2)
            return status, text
        else:
            return status, text

    async def _do_request(self, path, params, data, method, chunked, read_until_eof):
        async with self.session.request(
            method=method,
            url=f"{self.url}{path}",
            params=params,
            data=data,
            chunked=chunked,
            read_until_eof=read_until_eof,
        ) as response:
            return response.status, (await response.text())

    async def get_tokens(self, account_id):
        path = f"/admin/user/edit/o/5/u/{account_id}"
        status, text = await self.request(path, method="GET")
        if status == 200:

            def find_tokens_value(response_text):
                soup = BeautifulSoup(response_text, "lxml")
                return float(soup.find(attrs={"name": "tokens"})["value"])

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, find_tokens_value, text)
        else:
            return 0.0

    async def mod_tokens(self, mod_input):
        "mod_input list or str"
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

        def mod_tokens_result(response_text):
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
        else:
            return (
                None,
                f"Failed to modify tokens. Status code: {status}",
            )


def setup(bot):
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
