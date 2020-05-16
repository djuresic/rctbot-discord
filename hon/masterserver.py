import binascii
from hashlib import md5, sha256

import asyncio
import aiohttp
import discord
from discord.ext import commands

import utils.phpserialize as phpserialize
import srp

import core.perseverance
import core.config as config
from core.checks import is_tester, is_senior, in_whitelist, is_authenticated


class Masterserver:
    "Requires aiohttp.ClientSession()"

    usernames = {
        "ac": config.HON_USERNAME,
        "rc": config.HON_RC_USERNAME,
        "tc": config.HON_TC_USERNAME,
    }
    passwords = {
        "ac": config.HON_PASSWORD,
        "rc": config.HON_RC_PASSWORD,
        "tc": config.HON_TC_PASSWORD,
    }

    hostnames = {
        "ac": config.HON_NAEU_MASTERSERVER,
        "rc": config.HON_NAEU_RC_MASTERSERVER,
        "tc": config.HON_NAEU_TC_MASTERSERVER,
    }
    ua_versions = {
        "ac": config.HON_UA_VERSION,
        "rc": config.HON_UA_RC_VERSION,
        "tc": config.HON_UA_TC_VERSION,
    }
    client_os = {
        "ac": "ac",
        "rc": f"rc-{config.HON_NAEU_RC_OS_PART}",
        "tc": f"tc-{config.HON_NAEU_TC_OS_PART}",
    }
    client_names = {
        "ac": "Heroes of Newerth",
        "rc": "Heroes of Newerth Release Candidate",
        "tc": "Heroes of Newerth Private Test",
    }
    short_client_names = {"ac": "Retail", "rc": "RCT", "tc": "SBT"}
    colors = {"ac": 0x3CC03C, "rc": 0xFF6600, "tc": 0x0059FF}

    authentications = {"ac": False, "rc": False, "tc": False}
    cookies = {"ac": "None", "rc": None, "tc": None}  # class var
    ips = {"ac": None, "rc": None, "tc": None}
    auth_hashes = {"ac": None, "rc": None, "tc": None}
    chat_urls = {"ac": None, "rc": None, "tc": None}
    chat_ports = {"ac": None, "rc": None, "tc": None}
    account_ids = {"ac": None, "rc": None, "tc": None}
    nicknames = {"ac": None, "rc": None, "tc": None}

    def __init__(self, masterserver, session=None):
        self.session = session
        self.masterserver = masterserver

        self.username = self.usernames[masterserver]
        self.password = self.passwords[masterserver]

        self.hostname = self.hostnames[masterserver]
        self.ua_version = self.ua_versions[masterserver]
        self.client_name = self.client_names[masterserver]
        self.short_client_name = self.short_client_names[masterserver]
        self.color = self.colors[masterserver]

        self.authenticated = self.authentications[masterserver]
        self.cookie = self.cookies[masterserver]  # instance var
        self.ip = self.ips[masterserver]
        self.auth_hash = self.auth_hashes[masterserver]
        # add more

    async def close_session(self):
        return await self.session.close()

    async def prepare(self):
        "You are NOT prepared!"
        data = await self.authenticate(self.username, self.password)  # This is blocking

        try:
            self.cookie = self.cookies[self.masterserver] = data[b"cookie"].decode()
            # self.cookie = data[b"cookie"].decode()
            self.ip = self.ips[self.masterserver] = data[b"ip"].decode()
            self.auth_hash = self.auth_hashes[self.masterserver] = data[
                b"auth_hash"
            ].decode()
            self.chat_url = self.chat_urls[self.masterserver] = data[
                b"chat_url"
            ].decode()
            self.chat_port = self.chat_ports[self.masterserver] = int(
                data[b"chat_port"].decode()
            )
            self.account_id = self.account_ids[self.masterserver] = int(
                data[b"account_id"].decode()
            )
            self.nickname = self.nicknames[self.masterserver] = data[
                b"nickname"
            ].decode()

            self.authenticated = self.authentications[self.masterserver] = True
            # self.authenticated = True
            print(f"{self.short_client_name} authenticated!")
            return True

        except:
            self.authenticated = self.authentications[self.masterserver] = False
            # self.authenticated = False
            print(f"{self.short_client_name} failed to authenticate!")
            return False

    async def ensure_request(self, query, path=None, cookie=False, deserialize=True):
        if not self.authenticated and cookie:
            await self.prepare()
        response = await self.request(
            query, path=path, cookie=cookie, deserialize=deserialize
        )
        # if "cookie" in response[b"auth"].decode()
        if response and b"auth" in response and response[0] == False:
            for attempt in range(5):
                prepared = await self.prepare()
                if prepared:
                    return await self.request(
                        query, path=path, cookie=cookie, deserialize=deserialize
                    )
                else:
                    print(f"Preparation attempt {attempt+1} failed")
                await asyncio.sleep(attempt + 2)
            return response
        else:
            return response

    async def request(
        self, query, path=None, cookie=False, deserialize=True,
    ):  # default to RC masterserver instead
        # print(query)

        if path is None:
            path = "client_requester.php"

        if cookie:
            query["cookie"] = self.cookie

        headers = {
            "User-Agent": f"{config.HON_GAME_CLIENT}/{self.ua_version}/l{self.masterserver}/x86-biarch",
            "X-Forwarded-For": "unknown",
        }
        # print(headers)
        # print(query)

        async with self.session.get(
            "http://{0}/{1}".format(self.hostname, path), params=query, headers=headers
        ) as resp:
            try:
                data = await resp.text()
            except:
                print("Something went wrong while querying masterserver")
                return None  # False
            if deserialize:
                return phpserialize.loads(data.encode())
            else:
                return data

    async def authenticate(self, login, password):  # <3
        # session = aiohttp.ClientSession()
        # session = self.session
        login = login.lower()
        query = {"f": "pre_auth", "login": login}
        srp.rfc5054_enable()
        user = srp.User(
            login.encode(),
            None,
            hash_alg=srp.SHA256,
            ng_type=srp.NG_CUSTOM,
            n_hex=config.HON_S2_N.encode(),
            g_hex=config.HON_S2_G.encode(),
        )
        _, A = user.start_authentication()
        query["A"] = binascii.hexlify(A).decode()
        result = await self.request(query)
        if b"B" not in result:
            return result
        s = binascii.unhexlify(result[b"salt"])
        B = binascii.unhexlify(result[b"B"])
        salt2 = result[b"salt2"]
        user.password = (
            sha256(
                (
                    md5(
                        (md5(password.encode()).hexdigest()).encode()
                        + salt2
                        + config.HON_SRP_SS.encode()
                    ).hexdigest()
                ).encode()
                + config.HON_SRP_SL.encode()
            ).hexdigest()
        ).encode()
        user.p = user.password
        M = user.process_challenge(s, B)
        del query["A"]
        query["f"] = "srpAuth"
        query["proof"] = binascii.hexlify(M).decode()
        result = await self.request(query)
        # await session.close()
        # print(result)
        return result

    async def latest_client_version(self, client_os="windows", include_zero=False):
        """Client OS must be either Windows, macOS or Linux.
        Case insensitive and only the first letter matters. (w, m, l)
        
        include_zero displays the hotfix digit even if it is 0."""

        client_os = client_os[0].lower()
        os_parameter = f"{client_os}{self.client_os[self.masterserver]}"
        arch = {"w": "i686", "m": "universal", "l": "x86-biarch"}
        query = {"version": "0.0.0.0", "os": os_parameter, "arch": arch[client_os]}
        if include_zero:
            return (await self.request(query, "patcher/patcher.php"))[
                b"version"
            ].decode()
        else:
            return (await self.request(query, "patcher/patcher.php"))[0][
                b"version"
            ].decode()

    async def nick2id(self, nickname):
        result = await self.request({"f": "nick2id", "nickname[]": nickname.lower()})
        account_id = [
            value.lower() for value in result.values() if isinstance(value, bytes)
        ][
            0
        ]  # Not great
        cs_nickname = [key for key, value in result.items() if value == account_id][0]
        return {"nickname": cs_nickname.decode(), "account_id": account_id.decode()}

    async def id2nick(self, account_id):
        result = await self.request({"f": "id2nick", "account_id[]": account_id})
        try:
            nickname = result[int(account_id)]
        except:
            nickname = result
        return nickname

    async def show_stats(self, nickname, table):
        query = {"f": "show_stats", "nickname": nickname.lower(), "table": table}
        return await self.ensure_request(query, cookie=True)

    async def show_simple_stats(self, nickname):
        query = {"f": "show_simple_stats", "nickname": nickname.lower()}
        return await self.ensure_request(query)

    async def get_match_stats(self, match_id):
        query = {"f": "get_match_stats", "match_id[]": match_id}
        return await self.ensure_request(query, cookie=True)


class MasterserverTesting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sstats")
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def show_simple_stats(
        self, ctx, nickname=None, masterserver="ac"
    ):  # Dev purpose only
        """show_simple_stats"""

        if nickname is None:
            nickname = ctx.author.display_name

        async with aiohttp.ClientSession() as session:
            print(
                await Masterserver(masterserver, session=session).show_simple_stats(
                    nickname.lower()
                )
            )

    @commands.command(name="mstq")
    # @is_authenticated()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def get_match_stats(self, ctx, matchid: str, masterserver: str = "ac"):
        async with aiohttp.ClientSession() as session:
            match = await Masterserver(masterserver, session).get_match_stats(matchid)
            print(match)

    # dev
    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def id2nick(self, ctx, account_id: str, masterserver: str = "ac"):
        async with aiohttp.ClientSession() as session:
            ms = Masterserver(session, masterserver)
            result = await ms.id2nick(account_id)
        await ctx.send(
            f'Client: {ms.short_client_name}\nID: {account_id}\nNickname: **{result.decode() if result is not None and not isinstance(result, dict) else f"N/A {result}"}**'
        )  # This

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def nick2id(self, ctx, nickname: str, masterserver: str = "ac"):
        async with aiohttp.ClientSession() as session:
            ms = Masterserver(masterserver, session=session)
            result = await ms.nick2id(nickname)
        await ctx.send(
            f"Client: {ms.short_client_name}\nNickname: {result['nickname']}\nID: **{result['account_id']}**"
        )


def setup(bot):
    bot.add_cog(MasterserverTesting(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    # bot.remove_cog(MasterserverTesting(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
