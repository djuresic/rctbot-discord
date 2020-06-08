import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

import core.perseverance
import core.config as config
from core.webhooks import webhook_embed

from hon.masterserver import Client
from hon.avatar import get_avatar


# FIXME: Not singleton pattern.
class ACPClient:
    def __init__(self, masterserver="ac", session=None):
        if session is None:
            self.session = aiohttp.ClientSession(
                connector=ProxyConnector.from_url(config.HON_ACP_PROXY_URL)
            )
        else:
            self.session = session
        self.masterserver = masterserver
        self.url = None
        self.ssl = None

    # async def __aenter__(self) -> "ACPClient":
    async def __aenter__(self):
        await self.set_url_ssl(self.masterserver)
        await self.authenticate()
        return self

    # async def __aexit__(self, *_) -> None:
    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        await self.request("/logout.php", method="GET")
        await self.session.close()

    @staticmethod
    async def proxy_connector():
        "Returns ProxyConnector for use in ClientSession."
        return ProxyConnector.from_url(config.HON_ACP_PROXY_URL)

    async def set_url_ssl(self, masterserver):
        domain = config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
        if masterserver != "ac":
            self.url = f"http://{domain}"
            self.ssl = False
        else:
            self.url = f"https://{domain}"
            self.ssl = True
        # print(self.url, self.ssl)

    async def authenticate(self):
        status, text = await self.request(
            config.HON_ACP_AUTH, data=config.HON_ACP_MAGIC, ssl=self.ssl
        )
        if status in [200, 302] and config.HON_FORUM_USER in text:
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
        ssl=True,
    ):

        status, text = await self._do_request(
            path, params, data, method, chunked, read_until_eof, ssl
        )
        if status in [401, 403, 500]:
            for attempt in range(5):
                authenticated = await self.authenticate()
                if authenticated:
                    status, text = await self._do_request(
                        path, params, data, method, chunked, read_until_eof, ssl
                    )
                    return status, text
                else:
                    print(f"ACP authentication attempt {attempt+1} failed")
                await asyncio.sleep(attempt + 2)
            return status, text
        else:
            return status, text

    async def _do_request(
        self, path, params, data, method, chunked, read_until_eof, ssl
    ):
        async with self.session.request(
            method=method,
            url=f"{self.url}{path}",
            params=params,
            data=data,
            chunked=chunked,
            read_until_eof=read_until_eof,
            ssl=ssl,
        ) as response:
            return response.status, (await response.text())

    # TODO: Better way of doing this.
    async def log_action(self, ctx, account_id, action_verb, fields):
        admin_data = list(
            row for row in config.LIST_OF_LISTS if str(row[32]) == str(ctx.author.id)
        )[0]
        masterserver = Client(self.masterserver, session=self.session)
        nickname = await masterserver.id2nick(account_id)
        admin_icon = await get_avatar(admin_data[33])
        action = f"{admin_data[1]} ({admin_data[33]}) {action_verb} {nickname} ({account_id})."
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            masterserver.client_name,
            action,
            fields,
            admin_data[1],
            admin_icon,
        )

    async def get_sub_accounts(self, account_id):
        path = config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id}
        status, text = await self.request(
            path, params=query, method="GET", ssl=self.ssl
        )
        if status == 200:

            def find_accounts(response_text):
                soup = BeautifulSoup(response_text, "lxml")
                dropdown = soup.find(attrs={"id": "subAccountsList"})
                entries = dropdown.find_all("option")
                accounts = []
                for entry in entries:
                    accounts.append((int(entry["value"]), entry.text))
                return accounts

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, find_accounts, text)
        else:
            return None


def setup(bot):
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
