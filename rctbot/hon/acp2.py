import asyncio
import string
import secrets
import re
import ssl as ssl_module

import discord
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

import rctbot.config
from rctbot.core.webhooks import webhook_embed
from rctbot.core.driver import AsyncDatabaseHandler

from rctbot.hon.masterserver import Client
from rctbot.hon.utils import get_avatar

# TODO: Rearrange methods.
# TODO: Verify perks addition.

SSL_CONTEXT = ssl_module.create_default_context(purpose=ssl_module.Purpose.CLIENT_AUTH)
SSL_CONTEXT.load_cert_chain(certfile="lightwalker.crt.pem", keyfile="lightwalker.key.pem")

# FIXME: Not singleton pattern.
class ACPClient:
    """Interface for performing ACP tasks. Preferrably used as an asynchronous context manager."""

    ACP_CONFIG = {
        "ac": {"base_url": f"https://{rctbot.config.HON_ACP_AC_DOMAIN}", "color": 0x3CC03C},
        "rc": {"base_url": f"https://{rctbot.config.HON_ACP_RC_DOMAIN}", "color": 0xFF6600},
        "tc": {"base_url": f"http://{rctbot.config.HON_ACP_TC_DOMAIN}", "color": 0x0059FF},
    }

    def __init__(self, admin, masterserver="ac", session=None):
        if session is None:
            self.session = aiohttp.ClientSession(connector=ProxyConnector.from_url(rctbot.config.HON_ACP_PROXY_URL))
        else:
            self.session = session
        self.timeout = aiohttp.ClientTimeout(total=5 * 60, connect=None, sock_connect=None, sock_read=None)
        self.masterserver = masterserver
        self.url = self.ACP_CONFIG[masterserver]["base_url"]
        self.ssl = bool(self.url.startswith("https://"))
        if self.ssl and masterserver == "ac":
            self.ssl = SSL_CONTEXT
        self.color = self.ACP_CONFIG[masterserver]["color"]
        self.admin = admin
        self.db = AsyncDatabaseHandler.client[rctbot.config.MONGO_DATABASE_NAME]
        self.testers = self.db[rctbot.config.MONGO_TESTING_PLAYERS_COLLECTION_NAME]

    # async def __aenter__(self) -> "ACPClient":
    async def __aenter__(self):
        await self.authenticate()
        return self

    # async def __aexit__(self, *_) -> None:
    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        await self.request(rctbot.config.HON_ACP_DEAUTH, method="GET", ssl=self.ssl)
        await self.session.close()

    @staticmethod
    def proxy_connector():
        """Returns ProxyConnector for use in ClientSession."""
        return ProxyConnector.from_url(rctbot.config.HON_ACP_PROXY_URL)

    async def authenticate(self):
        status, _, text = await self.request(
            rctbot.config.HON_ACP_AUTH, data=rctbot.config.HON_ACP_MAGIC, ssl=self.ssl
        )
        return bool(status in [200, 301, 302] and rctbot.config.HON_ACP_USER in text)

    async def request(
        self,
        path,
        params=None,
        data=None,
        method="POST",
        allow_redirects=True,
        chunked=None,
        read_until_eof=True,
        ssl=True,
        timeout=None,
    ):
        if not timeout:
            timeout = self.timeout
        status, headers, text = await self._do_request(
            path, params, data, method, allow_redirects, chunked, read_until_eof, ssl, timeout,
        )
        if status in [401, 403, 500]:
            for attempt in range(5):
                authenticated = await self.authenticate()
                if authenticated:
                    status, headers, text = await self._do_request(
                        path, params, data, method, allow_redirects, chunked, read_until_eof, ssl, timeout,
                    )
                    return status, headers, text
                else:
                    print(f"ACP authentication attempt {attempt+1} failed")
                await asyncio.sleep(attempt + 2)
            return status, headers, text
        else:
            return status, headers, text

    async def _do_request(
        self, path, params, data, method, allow_redirects, chunked, read_until_eof, ssl, timeout,
    ):
        # print(self.url, path, params, data, method, chunked, read_until_eof, ssl)
        async with self.session.request(
            method=method,
            url=f"{self.url}{path}",
            params=params,
            data=data,
            allow_redirects=allow_redirects,
            chunked=chunked,
            read_until_eof=read_until_eof,
            ssl=ssl,
            timeout=timeout,
        ) as response:
            # print(response.status, response.headers, (await response.text()))
            return response.status, response.headers, (await response.text())

    # TODO: Better way of doing this.
    async def log_action(self, account_id, action_verb, fields):
        admin = await self.testers.find_one({"discord_id": self.admin.id})
        masterserver = Client(self.masterserver, session=self.session)
        if isinstance(account_id, str) and account_id.startswith("s"):
            nickname = "Unknown Nickname"
            account_id = account_id.replace("s", "Super ID ")
        else:
            nickname = await masterserver.id2nick(account_id)
        admin_icon = await get_avatar(admin["account_id"])
        # 1 Admin nickname 2 Admin aid or did
        action = (
            f'{discord.utils.escape_markdown(admin["nickname"])} ({admin["discord_id"]})'
            f" {action_verb} {discord.utils.escape_markdown(nickname)} ({account_id})."
        )
        await webhook_embed(
            rctbot.config.DISCORD_LOG_WEBHOOKS,
            masterserver.client_name,
            action,
            fields,
            admin["nickname"],  # Admin nickname
            admin_icon,
            color=self.color,
        )

    async def _search(self, search_path, search_by, search_for):
        search_data = {"search_by": search_by, "search_for": search_for}
        _, headers, _ = await self.request(search_path, data=search_data, allow_redirects=False, ssl=self.ssl)
        # Could use status here.
        if "Location" in headers:
            if "index." not in headers["Location"]:
                return "/" + headers["Location"]
            else:
                return None
        else:
            return None

    async def find_user_path(self, search_by, search_for):
        return await self._search(rctbot.config.HON_ACP_PROFILE_SEARCH, search_by, search_for)

    async def find_clan_path(self, search_by, search_for):
        return await self._search(rctbot.config.HON_ACP_CLAN_SEARCH, search_by, search_for)

    async def user_path_to_aid(self, user_path):
        """Return account_id from user profile path."""
        return int(user_path.split("aid=")[1])

    async def clan_path_to_cid(self, clan_path):
        """Return clan_id from clan path."""
        return int(clan_path.split("cid=")[1])

    async def nickname_to_aid(self, nickname):
        """Return account_id from nickname. None if it doesn't exist."""
        path = await self.find_user_path("nickname", nickname)
        if path:
            return await self.user_path_to_aid(path)
        else:
            return None

    async def sid_to_aid(self, super_id):
        """Return account_id from super_id. None if it doesn't exist."""
        path = await self.find_user_path("super_id", super_id)
        if path:
            return await self.user_path_to_aid(path)
        else:
            return None

    async def user_clan_data(self, clan_path, account_id):
        """Return tuple (tag, name, rank)."""
        *_, text = await self.request(clan_path, method="GET", ssl=self.ssl)

        def retrieve_data(response_text):
            soup = BeautifulSoup(response_text, features="lxml")
            clan_name = soup.find("input", attrs={"name": "clan_name"})["value"]
            clan_tag = soup.find("input", attrs={"name": "tag"})["value"]
            user_parent = soup.find("input", attrs={"name": "account_id", "value": str(account_id)}).parent
            clan_rank = user_parent.find("option", selected=True)["value"]
            # print(clan_rank)
            return clan_tag, clan_name, clan_rank

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, retrieve_data, text)

    async def get_sub_accounts(self, account_id):
        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id}
        status, _, text = await self.request(path, params=query, method="GET", ssl=self.ssl)
        fields = [
            {"name": "Fields", "value": "Sub-accounts", "inline": False},
        ]
        await self.log_action(account_id, "viewed", fields)
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

    async def check_suspension(self, super_id):
        path = rctbot.config.HON_ACP_SUSPENSION
        query = {"super_id": super_id}
        status, _, text = await self.request(path, params=query, method="GET", ssl=self.ssl)
        fields = [
            {"name": "Fields", "value": "Suspension", "inline": False},
        ]
        # account_id = await self.sid_to_aid(super_id) FIXME: broken for some reason
        await self.log_action(f"s{str(super_id)}", "viewed", fields)
        if status == 200:
            return text
        else:
            return None

    async def clan_invite(self, nickname, clan_tag=None):
        # TODO: Configurable clan tag.
        new_clan_tag = "RCT" if clan_tag is None else clan_tag
        new_clan_path = await self.find_clan_path("tag", new_clan_tag)
        if new_clan_path is None:
            return f"Clan with the tag {new_clan_tag} does not exist."
        new_clan_id = await self.clan_path_to_cid(new_clan_path)
        account_id = await self.nickname_to_aid(nickname)
        old_clan_path = await self.find_clan_path("nickname", nickname)
        # Set old clan data to None if the user wasn't in a clan.
        if not old_clan_path:
            old_clan_id = None
            old_clan_tag, old_clan_name, old_clan_rank = 3 * (None,)
        else:
            old_clan_id = await self.clan_path_to_cid(old_clan_path)
            old_clan_tag, old_clan_name, old_clan_rank = await self.user_clan_data(old_clan_path, account_id)
        if old_clan_id == new_clan_id:
            return f"{nickname} ({account_id}) is already in {old_clan_name} ({new_clan_id})"
        member_data = {"nickname": nickname}
        # Add to the new clan.
        status, *_ = await self.request(new_clan_path, data=member_data, ssl=self.ssl)
        # Fetch new data to check if it worked and log this action.
        new_clan_tag, new_clan_name, new_clan_rank = await self.user_clan_data(new_clan_path, account_id)
        # Set embedded fields.
        fields = [
            {"name": "Change", "value": f"Clan ({old_clan_id} -> {new_clan_id})", "inline": False,},
            {"name": "Old Tag", "value": old_clan_tag, "inline": True},
            {"name": "Old Name", "value": old_clan_name, "inline": True},
            {"name": "Old Rank", "value": old_clan_rank, "inline": True},
            {"name": "New Tag", "value": new_clan_tag, "inline": True},
            {"name": "New Name", "value": new_clan_name, "inline": True},
            {"name": "New Rank", "value": new_clan_rank, "inline": True},
        ]
        await self.log_action(account_id, "updated", fields)
        # This shouldn't be here...
        if status == 200:
            return f"Successfully added {nickname} ({account_id}) to {new_clan_name} ({new_clan_id})!"
        else:
            return None

    async def clan_remove(self, nickname):
        old_clan_path = await self.find_clan_path("nickname", nickname)
        account_id = await self.nickname_to_aid(nickname)
        if not old_clan_path:
            return f"{nickname} ({account_id}) is not in a clan!"
        old_clan_id = await self.clan_path_to_cid(old_clan_path)
        old_clan_tag, old_clan_name, old_clan_rank = await self.user_clan_data(old_clan_path, account_id)
        member_data = {"account_id": account_id, "rank": "Remove"}
        # Remove from clan.
        status, *_ = await self.request(old_clan_path, data=member_data, ssl=self.ssl)
        # Save time here by checking only the path and set embedded fields.
        await asyncio.sleep(0.1)
        new_clan_path = await self.find_clan_path("nickname", nickname)
        if new_clan_path:
            # In this case removal failed.
            return f"Failed to remove {nickname} ({account_id}) from {old_clan_name} ({old_clan_id})!"
        fields = [
            {"name": "Change", "value": f"Clan ({old_clan_id} -> {None})", "inline": False,},
            {"name": "Old Tag", "value": old_clan_tag, "inline": True},
            {"name": "Old Name", "value": old_clan_name, "inline": True},
            {"name": "Old Rank", "value": old_clan_rank, "inline": True},
            {"name": "New Tag", "value": None, "inline": True},
            {"name": "New Name", "value": None, "inline": True},
            {"name": "New Rank", "value": None, "inline": True},
        ]
        await self.log_action(account_id, "updated", fields)
        # This shouldn't be here...
        if status == 200:
            return f"Successfully removed {nickname} ({account_id}) from {old_clan_name} ({old_clan_id})!"
        else:
            return None

    async def clan_promote(self, nickname):
        clan_path = await self.find_clan_path("nickname", nickname)
        account_id = await self.nickname_to_aid(nickname)
        if not clan_path:
            return f"{nickname} ({account_id}) is not in a clan!"
        clan_id = await self.clan_path_to_cid(clan_path)
        *_, old_rank = await self.user_clan_data(clan_path, account_id)
        desired_rank = "Officer"
        if old_rank == desired_rank:
            return f"{nickname} ({account_id}) is already a Clan {desired_rank}."
        member_data = {"account_id": account_id, "rank": desired_rank}
        status, *_ = await self.request(clan_path, data=member_data, ssl=self.ssl)
        *_, new_rank = await self.user_clan_data(clan_path, account_id)
        fields = [
            {"name": "Change", "value": f"Clan ({clan_id})", "inline": False},
            {"name": "Old Rank", "value": old_rank, "inline": True},
            {"name": "New Rank", "value": new_rank, "inline": True},
        ]
        await self.log_action(account_id, "updated", fields)
        if status == 200 and new_rank == desired_rank:
            return f"Successfully promoted {nickname} ({account_id}) to Clan {new_rank}!"
        else:
            return None

    async def clan_demote(self, nickname):
        clan_path = await self.find_clan_path("nickname", nickname)
        account_id = await self.nickname_to_aid(nickname)
        if not clan_path:
            return f"{nickname} ({account_id}) is not in a clan!"
        clan_id = await self.clan_path_to_cid(clan_path)
        *_, old_rank = await self.user_clan_data(clan_path, account_id)
        desired_rank = "Member"
        if old_rank == desired_rank:
            return f"{nickname} ({account_id}) is already a Clan {desired_rank}."
        member_data = {"account_id": account_id, "rank": desired_rank}
        status, *_ = await self.request(clan_path, data=member_data, ssl=self.ssl)
        *_, new_rank = await self.user_clan_data(clan_path, account_id)
        fields = [
            {"name": "Change", "value": f"Clan ({clan_id})", "inline": False},
            {"name": "Old Rank", "value": old_rank, "inline": True},
            {"name": "New Rank", "value": new_rank, "inline": True},
        ]
        await self.log_action(account_id, "updated", fields)
        if status == 200 and new_rank == desired_rank:
            return f"Successfully demoted {nickname} ({account_id}) to Clan {new_rank}!"
        else:
            return None

    async def clan_crown(self, nickname):
        clan_path = await self.find_clan_path("nickname", nickname)
        account_id = await self.nickname_to_aid(nickname)
        if not clan_path:
            return f"{nickname} ({account_id}) is not in a clan!"
        clan_id = await self.clan_path_to_cid(clan_path)
        *_, old_rank = await self.user_clan_data(clan_path, account_id)
        desired_rank = "Leader"
        if old_rank == desired_rank:
            return f"{nickname} ({account_id}) is already a Clan {desired_rank}."
        member_data = {"account_id": account_id, "rank": desired_rank}
        status, *_ = await self.request(clan_path, data=member_data, ssl=self.ssl)
        *_, new_rank = await self.user_clan_data(clan_path, account_id)
        fields = [
            {"name": "Change", "value": f"Clan ({clan_id})", "inline": False},
            {"name": "Old Rank", "value": old_rank, "inline": True},
            {"name": "New Rank", "value": new_rank, "inline": True},
        ]
        await self.log_action(account_id, "updated", fields)
        if status == 200 and new_rank == desired_rank:
            return f"Successfully promoted {nickname} ({account_id}) to Clan {new_rank}!"
        else:
            return None

    async def add_perks(self, account_id):
        """Add RCT chat symbol and chat color to account."""
        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id}
        upgrades_data = {"give[product][]": ["2107", "918"], "upgradeya": "Add+Upgrade"}
        status, *_ = await self.request(path, params=query, data=upgrades_data, ssl=self.ssl)
        fields = [
            {"name": "Change", "value": "Upgrades", "inline": False},
            {"name": "Action", "value": "Add", "inline": True},
            {"name": "Items", "value": "cs.RCT\ncc.mentorwings", "inline": True},
        ]
        await self.log_action(account_id, "modified", fields)
        if status == 200:
            return f"Successfully gave RCT perks to {account_id}!"
        else:
            return None

    async def remove_perks(self, account_id):
        """Remove RCT chat symbol and chat color from account."""
        # FIXME: Unstable AF.
        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id}
        status, _, text = await self.request(path, params=query, method="GET", ssl=self.ssl)
        # This isn't good.
        if status == 200:

            def find_perks(response_text):
                soup = BeautifulSoup(response_text, features="lxml")
                chat_colors = soup.find_all("tr", attrs={"class": "Chat_Color_transdiv"})
                chat_symbols = soup.find_all("tr", attrs={"class": "Chat_Symbol_transdiv"})

                def find_values(table_tr, product_id):
                    td_list = []
                    product_id = str(product_id)
                    for tr in table_tr:
                        td = tr.find_all("td")
                        if td[3].text == product_id and td[0].span is None:
                            td_list.append((td[0].a["href"], td[1].text, td[2].text))
                    return td_list

                to_remove_cc = find_values(chat_colors, 918)
                to_remove_cs = find_values(chat_symbols, 2107)
                return to_remove_cc, to_remove_cs

            loop = asyncio.get_running_loop()
            cc_list, cs_list = await loop.run_in_executor(None, find_perks, text)
            await asyncio.sleep(0.5)
            all_upgrades = cc_list + cs_list
            if len(all_upgrades) == 0:
                return f"No RCT perks to remove for {account_id}."

            for upgrade in all_upgrades:
                # Refund URL index 0.
                await self.request(f"/{upgrade[0]}", method="GET", ssl=self.ssl)

            fields = [
                {"name": "Change", "value": "Upgrades", "inline": False},
                {"name": "Action", "value": "Removed", "inline": True},
                {"name": "Items", "value": "cs.RCT\ncc.mentorwings", "inline": True},
            ]
            await self.log_action(account_id, "modified", fields)
            return f"Removed a total of {len(all_upgrades)} RCT perk entries for {account_id}."
        else:
            return None

    @staticmethod
    def _get_account_info(response_text):
        """Return account infomation dictionary ready for further manipulation."""
        account_info = {}
        soup = BeautifulSoup(response_text, features="lxml")
        account_info["nickname"] = soup.find("input", attrs={"name": "nickname"})["value"]
        account_info["revert"] = ""
        account_info["password"] = ""
        account_info["email"] = soup.find("input", attrs={"name": "email"})["value"]
        account_info["first_name"] = soup.find("input", attrs={"name": "first_name"})["value"]
        account_info["last_name"] = soup.find("input", attrs={"name": "last_name"})["value"]
        account_info["address_1"] = soup.find("input", attrs={"name": "address_1"})["value"]
        account_info["address_2"] = soup.find("input", attrs={"name": "address_2"})["value"]
        account_info["city"] = soup.find("input", attrs={"name": "city"})["value"]
        account_info["region"] = soup.find("input", attrs={"name": "region"})["value"]
        account_info["postalcode"] = soup.find("input", attrs={"name": "postalcode"})["value"]
        country_options = soup.find("select", attrs={"name": "country"})
        try:
            account_info["country"] = country_options.find("option", selected=True)["value"]
        except TypeError:
            account_info["country"] = "USA"
        return account_info

    # FIXME: Blocks... everything.
    async def change_password(self, nickname, password):
        """Change password for nickname."""
        account_id = await self.nickname_to_aid(nickname)
        if account_id is None:
            return f"Could not change password for {nickname}. Account does not exist!"

        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id}
        *_, text = await self.request(path, params=query, method="GET", ssl=self.ssl)

        loop = asyncio.get_running_loop()
        account_info = await loop.run_in_executor(None, self._get_account_info, text)
        account_info["password"] = password
        admin = await self.testers.find_one({"discord_id": self.admin.id})
        account_info["note"] = f'RCTBot password change. Made by: {admin["nickname"]} ({admin["discord_id"]})'
        await self.request(path, params=query, data=account_info, ssl=self.ssl, allow_redirects=False)
        fields = [
            {"name": "Change", "value": "Account Information", "inline": False},
            {"name": "Type", "value": "Password", "inline": True},
        ]
        await self.log_action(account_id, "modified", fields)
        return f"Successfully changed password for {nickname} ({account_id})!"

    async def create_account(self, nickname):
        """Create an account. Nickname should but doesn't need to be case sensitive.
        \nReturns tuple (account_id, nickname, password). Values are None if failed."""
        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "create"}

        account_info = {"nickname": nickname}
        alphabet = string.ascii_letters + string.digits
        account_info["password"] = "".join(secrets.choice(alphabet) for i in range(8))
        account_info["email"] = "{}@{}.com".format(
            "".join(secrets.choice(alphabet) for i in range(16)), "".join(secrets.choice(alphabet) for i in range(8)),
        )
        # Status.
        _, headers, _ = await self.request(path, params=query, data=account_info, ssl=self.ssl, allow_redirects=False)
        if "Location" in headers:
            if "index." not in headers["Location"] and "error." not in headers["Location"]:
                path = "/" + headers["Location"]
            else:
                path = None
        else:
            path = None
        if path:
            # print(path)
            account_id = await self.user_path_to_aid(path)
            await self.log_action(account_id, "created", [])
            return account_id, nickname, account_info["password"]
        else:
            return 3 * (None,)

    async def user_test_access(self, account_id):
        """Get test access field for account."""
        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id}
        *_, text = await self.request(path, params=query, method="GET", ssl=self.ssl)

        def find_access(response_text):
            soup = BeautifulSoup(response_text, features="lxml")
            return soup.find("a", attrs={"href": re.compile("test_access")}).parent.b.string

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, find_access, text)

    async def toggle_test_access(self, account_id):
        """Toggle Test Access. Returns success bool."""
        path = rctbot.config.HON_ACP_PROFILE
        query = {"f": "modify", "aid": account_id, "toggle": "test_access"}
        _, headers, _ = await self.request(path, params=query, ssl=self.ssl, allow_redirects=False)
        if "Location" in headers:
            return bool("index." not in headers["Location"] and "error." not in headers["Location"])
        else:
            return False


# pylint: disable=unused-argument
def setup(bot):
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
