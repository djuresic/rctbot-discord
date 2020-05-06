import string
import secrets
import asyncio
from functools import partial

import aiohttp
from aiohttp_socks import ProxyConnector
from discord.utils import escape_markdown

from utils.honavatar import get_avatar

import config
from extensions.masterserver import nick2id
from extensions.webhooks import webhook_embed

# Switch from nick2id to config and spreadsheet.


async def get_url_ssl(masterserver="ac"):
    "Returns tuple URL, SSL for masterserver."
    _domain = config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
    if masterserver != "ac":
        _url = f"http://{_domain}"
        _ssl = False
    else:
        _url = f"https://{_domain}"
        _ssl = True
    # print(_url, _ssl)
    return _url, _ssl


async def proxy_connector():
    "Returns ProxyConnector for use in ClientSession."
    return ProxyConnector.from_url(config.HON_ACP_PROXY_URL)


# TC auth fails
async def authenticate(session, masterserver="ac"):
    url, ssl = await get_url_ssl(masterserver)
    url = url + config.HON_ACP_AUTH
    # await session.get(url, ssl=ssl)
    async with session.post(url, data=config.HON_ACP_MAGIC, ssl=ssl) as resp:
        # print(await resp.text())
        if "Restricted Content" in (await resp.text()):
            return 403
        else:
            return resp.status


# Enable for other clans, restriction in command itself instead
# Needs clan and rank from masterserver, use .lu for now
async def add_member(session, nickname, admin, masterserver="ac"):
    "Adds a clan member."
    if masterserver == "ac":
        clan_id = "126869"
    else:
        clan_id = "106824"
    url, ssl = await get_url_ssl(masterserver)
    url = url + config.HON_ACP_CLAN
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    query = {"f": "modify", "cid": clan_id}
    member_data = {"nickname": nickname}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_avatar(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old ID", "value": "Not Available", "inline": True},
        {"name": "Old Tag", "value": "Not Available", "inline": True},
        {"name": "Old Name", "value": "Not Available", "inline": True},
        {"name": "New ID", "value": clan_id, "inline": True},
        {"name": "New Tag", "value": "[RCT]", "inline": True},
        {"name": "New Name", "value": "Retail Candidate Testers", "inline": True},
    ]
    async with session.post(url, params=query, data=member_data, ssl=ssl) as resp:
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            config.HON_MASTERSERVER_INFO[masterserver]["client"],
            action,
            fields,
            admin_data[1],
            admin_icon,
        )
        return resp.status


# No need for rank
async def remove_member(session, nickname, admin, masterserver="ac"):
    "Removes a clan member."
    if masterserver == "ac":
        clan_id = "126869"
    else:
        clan_id = "106824"
    url, ssl = await get_url_ssl(masterserver)
    url = url + config.HON_ACP_CLAN
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    query = {"f": "modify", "cid": clan_id}
    member_data = {"account_id": account_id, "rank": "Remove"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_avatar(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old ID", "value": clan_id, "inline": True},
        {"name": "Old Tag", "value": "[RCT]", "inline": True},
        {"name": "Old Name", "value": "Retail Candidate Testers", "inline": True},
        {"name": "New ID", "value": "0", "inline": True},
        {"name": "New Tag", "value": "None", "inline": True},
        {"name": "New Name", "value": "None", "inline": True},
    ]
    async with session.post(url, params=query, data=member_data, ssl=ssl) as resp:
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            config.HON_MASTERSERVER_INFO[masterserver]["client"],
            action,
            fields,
            admin_data[1],
            admin_icon,
        )
        return resp.status


# Get old rank from masterserver
async def promote_member(session, nickname, admin, masterserver="ac"):
    "Promotes clan member to Officer."
    if masterserver == "ac":
        clan_id = "126869"
    else:
        clan_id = "106824"
    url, ssl = await get_url_ssl(masterserver)
    url = url + config.HON_ACP_CLAN
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    query = {"f": "modify", "cid": clan_id}
    member_data = {"account_id": account_id, "rank": "Officer"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_avatar(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old Rank", "value": "Not Available", "inline": True},
        {"name": "New Rank", "value": "Officer", "inline": True},
    ]
    async with session.post(url, params=query, data=member_data, ssl=ssl) as resp:
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            config.HON_MASTERSERVER_INFO[masterserver]["client"],
            action,
            fields,
            admin_data[1],
            admin_icon,
        )
        return resp.status


# Get old rank from masterserver
async def demote_member(session, nickname, admin, masterserver="ac"):
    "Demotes clan member to Member."
    if masterserver == "ac":
        clan_id = "126869"
    else:
        clan_id = "106824"
    url, ssl = await get_url_ssl(masterserver)
    url = url + config.HON_ACP_CLAN
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    query = {"f": "modify", "cid": clan_id}
    member_data = {"account_id": account_id, "rank": "Member"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_avatar(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old Rank", "value": "Not Available", "inline": True},
        {"name": "New Rank", "value": "Member", "inline": True},
    ]
    async with session.post(url, params=query, data=member_data, ssl=ssl) as resp:
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            config.HON_MASTERSERVER_INFO[masterserver]["client"],
            action,
            fields,
            admin_data[1],
            admin_icon,
        )
        return resp.status


# Must have temp prevention of use for the same nick per command to avoid duplicates of items.
async def add_perks(session, nickname, admin):
    "Adds RCT chat symbol and chat color to account."
    url, ssl = await get_url_ssl()
    url = url + config.HON_ACP_PROFILE
    result = await nick2id(nickname)
    nickname = result["nickname"]
    account_id = result["account_id"]
    query = {"f": "modify", "aid": account_id}
    upgrades_data = {"give[product][]": ["2107", "918"], "upgradeya": "Add+Upgrade"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_avatar(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Upgrades", "inline": False},
        {"name": "Action", "value": "Add", "inline": True},
        {"name": "Items", "value": "cs.RCT\ncc.mentorwings", "inline": True},
    ]
    async with session.post(url, params=query, data=upgrades_data, ssl=ssl) as resp:
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            config.HON_MASTERSERVER_INFO["ac"]["client"],
            action,
            fields,
            admin_data[1],
            admin_icon,
        )
        return resp.status


# Incomplete
async def remove_perks(session, nickname, admin):
    "Removes RCT chat symbol and chat color from account."
    fields = [
        {"name": "Change", "value": "Upgrades", "inline": False},
        {"name": "Action", "value": "Remove", "inline": True},
        {"name": "Items", "value": "cs.RCT\ncc.mentorwings", "inline": True},
    ]
    pass


async def change_password(session, nickname, password, admin):
    "Changes password for test clients only."
    masterserver = "tc"
    url, ssl = await get_url_ssl(masterserver)
    url = url + config.HON_ACP_PROFILE
    print(url, ssl)
    result = await nick2id(nickname, masterserver=masterserver)
    print(result)
    nickname = result["nickname"]
    account_id = result["account_id"]

    query = {"f": "modify", "aid": account_id}
    account_data = config.HON_ACP_ACCOUNT_INFO_MAGIC.copy()
    account_data["nickname"] = nickname
    account_data["password"] = password

    alphabet = string.ascii_letters + string.digits
    account_data["email"] = "{}@{}.com".format(
        "".join(secrets.choice(alphabet) for i in range(16)),
        "".join(secrets.choice(alphabet) for i in range(8)),
    )
    account_data["note"] = "RCTBot+password+change"
    # return print(account_data)
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_avatar(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Account", "inline": False},
        {"name": "Type", "value": "Password", "inline": True},
    ]
    async with session.post(url, params=query, data=account_data, ssl=ssl) as resp:
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            config.HON_MASTERSERVER_INFO[masterserver]["client"],
            action,
            fields,
            admin_data[1],
            admin_icon,
        )
        print(await resp.text())
        return resp.status


def setup(bot):
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
