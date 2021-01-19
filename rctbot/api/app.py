"""
RCTBot A Discord bot with Heroes of Newerth integration.
Copyright (C) 2020–2021  Danijel Jurešić

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "0.3.1"

import json
import asyncio
from datetime import datetime, timezone

import discord
from fastapi import FastAPI, status  # starlette.status

# from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth, OAuthError

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler
from rctbot.hon.masterserver import authenticate

# TODO
class API:
    bot = None
    app = None


config = Config(".env")

app = FastAPI(title="RCTBot API", description="desc", version=__version__, debug=False)
app.add_middleware(SessionMiddleware, secret_key=config.get("SSM_SECRET_KEY"))
app.mount("/static", StaticFiles(directory="rctbot/api/static"), name="static")

templates = Jinja2Templates(directory="rctbot/api/templates")

oauth = OAuth()
oauth.register(
    name="discord",
    client_id=config.get("DISCORD_CLIENT_ID"),
    client_secret=config.get("DISCORD_CLIENT_SECRET"),
    authorize_url="https://discord.com/api/oauth2/authorize",
    authorize_params=None,
    access_token_url="https://discord.com/api/oauth2/token",
    access_token_params=None,
    # revocation_endpoint="https://discord.com/api/oauth2/token/revoke",
    api_base_url="https://discord.com/api/",
    client_kwargs={"token_endpoint_auth_method": "client_secret_post", "scope": "identify"},
)


@app.route("/")
async def homepage(request: Request):
    user = request.session.get("user")
    if not user:
        return templates.TemplateResponse("signin.html", {"request": request})
    if hon_connected := bool("hon" in user):
        hon_data = user["hon"]
        hon_message = f'Your HoN account {hon_data["username"]} ({hon_data["account_id"]}) is connected.'
    else:
        hon_message = "You don't have a HoN account connected. Let's change that!"
    return templates.TemplateResponse(
        "signin.html",
        {
            "request": request,
            "user": user,
            "hon_message": hon_message,
            "hon_connected": hon_connected,
            "auth": user.pop("auth", None),
        },
    )


@app.route("/login/discord")
async def login_discord(request: Request):
    # print(request.url_for("auth_discord"))
    redirect_uri = f'{config.get("DOMAIN")}/auth/discord'
    return await oauth.discord.authorize_redirect(request, redirect_uri)


@app.route("/login/hon")
async def login_hon(request: Request):
    user = request.session.get("user")
    if not user or "hon" in user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        "signin_hon.html", {"request": request, "user": user, "auth": user.pop("auth", None)},
    )


# return JSONResponse({"detail": "Not Found"}, status_code=404)


@app.route("/auth/discord")
async def auth_discord(request: Request):
    try:
        token = await oauth.discord.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f"<h1>{error}</h1>")
    resp = await oauth.discord.get(
        "users/@me", token=token, headers={"User-Agent": f"RCTBot ({API.bot.repository_url}, {API.bot.version})"}
    )
    profile = dict(resp.json())
    if "avatar" in profile:
        src = "https://cdn.discordapp.com/avatars/{}/{}.png"
        profile["picture"] = src.format(profile["id"], profile["avatar"])
    else:
        profile["picture"] = "https://discord.com/assets/6debd47ed13483642cf09e832ed0bc1b.png"  # TODO: function
    request.session["user"] = profile
    collection = AsyncDatabaseHandler.client["rctbot"]["users"]
    if not (
        account := await collection.find_one(
            {"discord_id": int(profile["id"])}, {"_id": 0, "username": 1, "account_id": 1, "super_id": 1}
        )
    ):
        return RedirectResponse(url="/login/hon")
    request.session["user"]["hon"] = account
    return RedirectResponse(url="/")


@app.route("/auth/hon", methods=["POST"])
async def auth_hon(request: Request):
    user = request.session.get("user")
    if not user or "hon" in user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    data = await request.form()
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, authenticate, data["username"], data["password"])
    date = datetime.now(timezone.utc)
    # TODO: not in
    if b"account_id" in data:
        discord_id = int(user["id"])
        # TODO: Remove hardcoded database and collection names.
        collection = AsyncDatabaseHandler.client["rctbot"]["users"]
        testers_collection = AsyncDatabaseHandler.client["rct"]["testers"]
        if await collection.find_one({"discord_id": discord_id}):
            # It can't go this wrong, can it?
            return RedirectResponse(url="/logout", status_code=status.HTTP_303_SEE_OTHER)
        username = data[b"nickname"].decode()
        account_id = int(data[b"account_id"].decode())
        super_id = int(data[b"super_id"].decode())
        if (existing := await collection.find_one({"super_id": super_id})) :
            request.session["user"]["auth"] = {
                "alert": "warning",
                "message": (
                    f"Unable to connect {username} ({account_id})!"
                    f' Your account {existing["username"]} ({existing["account_id"]})'
                    " is already linked to a Discord account."
                ),
            }
            return RedirectResponse(url="/login/hon", status_code=status.HTTP_303_SEE_OTHER)
        account = {
            "username": username,
            "account_id": account_id,
            "super_id": super_id,
        }
        request.session["user"]["hon"] = json.loads(json.dumps(account))  # FIXME: What happened here?
        account["discord_id"] = discord_id
        account["date"] = date
        account["application_ip"] = data[b"ip"].decode()
        result = await collection.insert_one(account)
        if result.acknowledged:
            request.session["user"]["auth"] = {"alert": "success", "message": "HoN Account linked successfully!"}

            tester_document = await testers_collection.find_one(
                {"enabled": True, "super_id": super_id}, {"_id": 0, "discord_id": 1}
            )
            if tester_document and not tester_document["discord_id"]:
                # Missing acknowledged check.
                await testers_collection.update_one(
                    {"super_id": super_id}, {"$set": {"discord_id": discord_id}},
                )

            guild = API.bot.get_guild(rctbot.config.DISCORD_RCT_GUILD_ID)
            if member := guild.get_member(discord_id):
                community = discord.utils.get(guild.roles, name="Community Member")
                if community not in member.roles:
                    await member.add_roles(community, reason="Linked Heroes of Newerth.")

                if tester_document:
                    tester = discord.utils.get(guild.roles, name="Tester")
                    if tester not in member.roles:
                        await member.add_roles(tester, reason="Linked Heroes of Newerth as a Tester.")

        else:
            request.session["user"]["auth"] = {
                "alert": "danger",
                "message": "Could not link HoN Account, please log out and try again.",
            }

    else:
        request.session["user"]["auth"] = {"alert": "danger", "message": data[b"auth"].decode()}
    return RedirectResponse(url="/login/hon", status_code=status.HTTP_303_SEE_OTHER)


@app.route("/logout", methods=["GET", "POST"])
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/users/me")
async def read_user_me(request: Request):
    user = request.session.get("user")
    if not user:
        return {"user_id": None}
    return {"user_id": user.get("id", None)}


# NOTE: /docs
@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
