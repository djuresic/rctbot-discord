"""
Interacts with the Heroes of Newerth forums.
"""

import aiohttp
from time import time
from hashlib import md5

import discord
from discord.ext import commands

import core.perseverance
import core.config as config

# Move to a new module.
async def login_ipb(session):
    """Log into the Heroes of Newerth forums."""
    index = "https://forums.heroesofnewerth.com/index.php"

    async with session.get(index) as resp:
        index_get = await resp.text()
        csrf_key = index_get.split('csrfKey: "')[1].split('"')[0]

    login_params = {"/login/": ""}
    login_data = {
        "csrfKey": csrf_key,
        "auth": config.HON_FORUM_USER,
        "password": config.HON_FORUM_USER_PASSWORD,
        "_processLogin": ["usernamepassword", "usernamepassword"],
    }

    async with session.post(index, params=login_params, data=login_data) as resp:
        await resp.text()
    return csrf_key


async def login(session):
    """Log into the Heroes of Newerth forums."""
    login_url = "https://forums.heroesofnewerth.com/login.php"
    login_params = {"do": "login"}
    login_data = {
        "cookieuser": "1",
        "do": "login",
        "s": "",
        "securitytoken": "guest",
        "vb_login_md5password": config.HON_FORUM_USER_MD5_PASSWORD,
        "vb_login_md5password_utf": config.HON_FORUM_USER_MD5_PASSWORD,
        "vb_login_password": "",
        "vb_login_password_hint": "Password",
        "vb_login_username": config.HON_FORUM_USER,
    }
    async with session.post(login_url, params=login_params, data=login_data) as resp:
        return await resp.text()


async def get_security_token(session):
    """Get this session's security token."""
    index = "https://forums.heroesofnewerth.com/index.php"
    async with session.get(index) as resp:
        index_get = await resp.text()
        return index_get.split('SECURITYTOKEN = "')[1][:51]


async def new_thread(session, subforum_id, subject, message, security_token=None):
    """Create a new thread."""
    if security_token is None:
        security_token = await get_security_token(session)
    post_hash = md5(message.encode("utf-8")).hexdigest()  # "This is fine."
    post_start_time = str(int(time()))
    new_thread_url = "https://forums.heroesofnewerth.com/newthread.php"
    thread_params = {"do": "postthread", "f": subforum_id}
    thread_data = {
        "do": "postthread",
        "f": subforum_id,
        "iconid": "0",
        "loggedinuser": config.HON_FORUM_USER_ACCOUNT_ID,
        "message": message,
        "message_backup": message,
        "parseurl": "1",
        "posthash": post_hash,
        "poststarttime": post_start_time,
        "prefixid": "",
        "s": "",
        "sbutton": "Submit+New+Thread",
        "securitytoken": security_token,
        "signature": "1",
        "subject": subject,
        "until": "0",
        "wysiwyg": "0",
    }
    async with session.post(
        new_thread_url, params=thread_params, data=thread_data
    ) as resp:
        return await resp.text()


async def new_reply(session, thread_id, message, security_token=None):
    """Reply to an existing thread."""
    if security_token is None:
        security_token = await get_security_token(session)
    post_hash = md5(message.encode("utf-8")).hexdigest()  # "This is fine."
    post_start_time = str(int(time()))
    new_reply_url = "https://forums.heroesofnewerth.com/newreply.php"
    post_params = {"do": "postreply", "t": thread_id}
    post_data = {
        "ajax": "1",
        "ajax_lastpost": "",
        "do": "postreply",
        "fromquickreply": "1",
        "loggedinuser": config.HON_FORUM_USER_ACCOUNT_ID,
        "message": message,
        "message_backup": message,
        "p": "who cares",
        "parseurl": "1",
        "post_as": config.HON_FORUM_USER_ACCOUNT_ID,
        "posthash": post_hash,
        "poststarttime": post_start_time,
        "s": "",
        "securitytoken": security_token,
        "signature": "1",
        "specifiedpost": "0",
        "t": thread_id,
        "wysiwyg": "0",
    }
    async with session.post(new_reply_url, params=post_params, data=post_data) as resp:
        return await resp.text()


async def edit_post(session, post_id, title, message, reason, security_token=None):
    """Edit a post."""
    if security_token is None:
        security_token = await get_security_token(session)
    post_hash = md5(message.encode("utf-8")).hexdigest()  # "This is fine."
    post_start_time = str(int(time()))
    edit_post_url = "https://forums.heroesofnewerth.com/editpost.php"
    post_params = {"do": "updatepost", "p": post_id}
    post_data = {
        "do": "updatepost",
        "iconid": "0",
        "message": message,
        "message_backup": message,
        "p": post_id,
        "parseurl": "1",
        "posthash": post_hash,
        "poststarttime": post_start_time,
        "prefixid": "",
        "reason": reason,
        "s": "",
        "sbutton": "Save+Changes",
        "securitytoken": security_token,
        "signature": "1",
        "title": title,
        "until": "0",
        "wysiwyg": "0",
    }
    async with session.post(edit_post_url, params=post_params, data=post_data) as resp:
        return await resp.text()


def setup(bot):
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
