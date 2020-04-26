import aiohttp
from aiohttp_socks import ProxyConnector
from discord.utils import escape_markdown

import config
from extensions.masterserver import nick2id
from extensions.webhooks import webhook_embed

# Switch from nick2id to config and spreadsheet.

# This should be moved to extensions.masterserver
async def get_cai(account_id=None):
    if account_id is not None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://hon-avatar.now.sh/{account_id}") as resp:
                account_icon_url = await resp.text()
                if not account_icon_url.endswith(".cai"):
                    account_icon_url = "https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png"
    else:
        account_icon_url = (
            "https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png"
        )
    return account_icon_url


async def proxy_connector():
    return ProxyConnector.from_url(config.HON_ACP_PROXY_URL)


async def authenticate(session, masterserver="ac"):
    if masterserver != "ac":
        ssl = False
    else:
        ssl = True
    async with session.post(
        config.HON_ACP_AUTH.format(
            domain=config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
        ),
        data=config.HON_ACP_MAGIC,
        ssl=ssl,
    ) as resp:
        if "Restricted Content" in (await resp.text()):
            return 403
        else:
            return resp.status


# Enable for other clans, restriction in command itself instead
# Needs clan and rank from masterserver, use .lu for now
async def add_member(session, nickname, admin, masterserver="ac"):
    if masterserver != "ac":
        ssl = False
    else:
        ssl = True
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    member_data = {"nickname": nickname}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_cai(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old ID", "value": "Not Available", "inline": True},
        {"name": "Old Tag", "value": "Not Available", "inline": True},
        {"name": "Old Name", "value": "Not Available", "inline": True},
        {"name": "New ID", "value": "126869", "inline": True},
        {"name": "New Tag", "value": "[RCT]", "inline": True},
        {"name": "New Name", "value": "Retail Candidate Testers", "inline": True},
    ]
    async with session.post(
        config.HON_ACP_CLAN.format(
            domain=config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
        ),
        data=member_data,
        ssl=ssl,
    ) as resp:
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
    if masterserver != "ac":
        ssl = False
    else:
        ssl = True
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    member_data = {"account_id": account_id, "rank": "Remove"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_cai(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old ID", "value": "126869", "inline": True},
        {"name": "Old Tag", "value": "[RCT]", "inline": True},
        {"name": "Old Name", "value": "Retail Candidate Testers", "inline": True},
        {"name": "New ID", "value": "0", "inline": True},
        {"name": "New Tag", "value": "None", "inline": True},
        {"name": "New Name", "value": "None", "inline": True},
    ]
    async with session.post(
        config.HON_ACP_CLAN.format(
            domain=config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
        ),
        data=member_data,
        ssl=ssl,
    ) as resp:
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
    if masterserver != "ac":
        ssl = False
    else:
        ssl = True
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    member_data = {"account_id": account_id, "rank": "Officer"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_cai(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old Rank", "value": "Not Available", "inline": True},
        {"name": "New Rank", "value": "Officer", "inline": True},
    ]
    async with session.post(
        config.HON_ACP_CLAN.format(
            domain=config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
        ),
        data=member_data,
        ssl=ssl,
    ) as resp:
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
    if masterserver != "ac":
        ssl = False
    else:
        ssl = True
    result = await nick2id(nickname, masterserver=masterserver)
    nickname = result["nickname"]
    account_id = result["account_id"]
    member_data = {"account_id": account_id, "rank": "Member"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_cai(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Clan", "inline": False},
        {"name": "Old Rank", "value": "Not Available", "inline": True},
        {"name": "New Rank", "value": "Member", "inline": True},
    ]
    async with session.post(
        config.HON_ACP_CLAN.format(
            domain=config.HON_MASTERSERVER_INFO[masterserver]["acp_domain"]
        ),
        data=member_data,
        ssl=ssl,
    ) as resp:
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
    result = await nick2id(nickname)
    nickname = result["nickname"]
    account_id = result["account_id"]
    upgrades_data = {"give[product][]": ["2107", "918"], "upgradeya": "Add+Upgrade"}
    admin_data = list(
        row for row in config.LIST_OF_LISTS if str(row[32]) == str(admin.id)
    )[0]
    admin_icon = await get_cai(admin_data[33])
    action = f"{admin_data[1]} ({admin_data[33]}) updated {nickname} ({account_id})."
    fields = [
        {"name": "Change", "value": "Upgrades", "inline": False},
        {"name": "Action", "value": "Add", "inline": True},
        {"name": "Items", "value": "cs.RCT\ncc.mentorwings", "inline": True},
    ]
    async with session.post(
        config.HON_ACP_ADD_PERKS.format(
            domain=config.HON_ACP_AC_DOMAIN, account_id=account_id
        ),
        data=upgrades_data,
    ) as resp:
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
    fields = [
        {"name": "Change", "value": "Upgrades", "inline": False},
        {"name": "Action", "value": "Remove", "inline": True},
        {"name": "Items", "value": "cs.RCT\ncc.mentorwings", "inline": True},
    ]
    pass


async def change_password(session, nickname, password, admin):
    fields = [
        {"name": "Change", "value": "Account", "inline": False},
        {"name": "Type", "value": "Password", "inline": True},
    ]
    pass


def setup(bot):
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.BOT_LOADED_EXTENSIONS.remove(__loader__.name)
