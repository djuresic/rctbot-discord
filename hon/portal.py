import aiohttp
import asyncio

import core.perseverance
import core.config as config

# TO DO: Use Beautiful Soup


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
        status, response = await self.request("/auth", method="GET")
        right_part = response.split('name="_token" value="')[1]
        token = right_part.split('">')[0]
        self.token = token

        data = {
            "_token": self.token,
            "password": config.HON_FORUM_USER_PASSWORD,
            "username": config.HON_FORUM_USER,
        }

        status, response = await self.request("/auth/login", data=data)
        if status == 200 and "RCTBot" in response:
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

        status, response = await self._do_request(
            path, params, data, method, chunked, read_until_eof
        )
        if status in [401, 403, 500]:
            for attempt in range(5):
                authenticated = await self.authenticate()
                if authenticated:
                    status, response = await self._do_request(
                        path, params, data, method, chunked, read_until_eof
                    )
                    return status, response
                else:
                    print(f"Portal authentication attempt {attempt+1} failed")
                await asyncio.sleep(attempt + 2)
            return status, response
        else:
            return status, response

    async def _do_request(self, path, params, data, method, chunked, read_until_eof):
        async with self.session.request(
            method=method,
            url=f"{self.url}{path}",
            params=params,
            data=data,
            chunked=chunked,
            read_until_eof=read_until_eof,
        ) as resp:
            return resp.status, (await resp.text())

    async def get_tokens(self, account_id):
        path = f"/admin/user/edit/o/5/u/{account_id}"
        status, response = await self.request(path, method="GET")
        if status == 200:
            right_part = response.split(
                'placeholder="Enter tokens" autocomplete="off" value="'
            )[1]
            tokens = right_part.split('">')[0]
            return float(tokens)
        else:
            return 0

    async def mod_tokens(self, input_list):
        path = "/admin/tokens/mod/o/5"
        data = {
            "_token": self.token,
            "modInput": "\n".join(input_list),
        }
        return await self.request(path, data=data)


def setup(bot):
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
