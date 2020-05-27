import aiohttp
from aiohttp import web

import discord
from discord.ext import commands

import core.perseverance
import core.config as config
from core.checks import in_whitelist

from hon.masterserver import Client
from extensions.testing import game_hosted, cc_detected


async def web_server(bot):
    await bot.wait_until_ready()

    routes = web.RouteTableDef()

    @routes.get("/")
    async def _hello_world(request):
        return web.Response(text=f"Hello, World! {config.WEB_DOMAIN} - OK")

    @routes.get("/hon/{nickname}/id")
    async def _hon_id(request):
        nickname = request.match_info["nickname"]
        async with aiohttp.ClientSession() as session:
            response = await Client("ac", session=session).show_stats(
                nickname, "ranked"
            )
            if not response or b"account_id" not in response:
                return web.Response(text="404: Not Found", status=404)
            data = {
                "aid": int(response[b"account_id"].decode()),
                "sid": int(response[b"super_id"].decode()),
            }
        return web.json_response(data)

    @routes.post(config.WEB_GAME_LOBBY_PATH)
    async def _game_lobby(request):  # POST handler for game lobbies
        data = await request.post()
        # print(data)
        try:
            token = data["token"]
        except:
            print(f"401: Unauthorized {config.WEB_GAME_LOBBY_PATH}")
            return web.Response(text="401: Unauthorized", status=401)

        if token != config.WEB_TOKEN:
            print(f"403: Forbidden {config.WEB_GAME_LOBBY_PATH}")
            return web.Response(text="403: Forbidden", status=403)

        try:
            lobby_name = data["match_name"]
            match_id = data["match_id"]
            await game_hosted(bot, lobby_name, match_id)
            return web.Response(text="OK")
        except:
            return web.Response(text="400: Bad Request", status=400)
        # return web.Response(body='data: {}'.format(a))

    @routes.post(config.WEB_CHAT_COLOR_PATH)
    async def _chat_color(request):  # POST handler for cc upgrade
        data = await request.post()
        # print(data)
        try:
            token = data["token"]
        except:
            print(f"401: Unauthorized {config.WEB_CHAT_COLOR_PATH}")
            return web.Response(text="401: Unauthorized", status=401)

        if token != config.WEB_TOKEN:
            print(f"403: Forbidden {config.WEB_CHAT_COLOR_PATH}")
            return web.Response(text="403: Forbidden", status=403)

        try:
            _nickname = data["nickname"]
            _account_id = data["account_id"]
            await cc_detected(bot, _nickname, _account_id)
            return web.Response(text="OK")
        except:
            return web.Response(text="400: Bad Request", status=400)

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.WEB_LOCAL_IP, config.WEB_LOCAL_PORT)
    await site.start()
    print(
        f"Web server started on {config.WEB_LOCAL_IP}:{config.WEB_LOCAL_PORT} ({config.WEB_DOMAIN})."
    )


class Web(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {
                "token": config.WEB_TOKEN,
                "match_name": "RCT with Lightwalker",
                "match_id": "1337",
            }
            async with session.post(
                f"https://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}", data=data
            ) as resp:
                await resp.text()

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post_insecure(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {
                "token": config.WEB_TOKEN,
                "match_name": "RCT with Lightwalker",
                "match_id": "1337",
            }
            async with session.post(
                f"http://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}", data=data
            ) as resp:
                await resp.text()

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post_nopw(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {"match_name": "RCT with Lightwalker", "match_id": "1337"}
            async with session.post(
                f"https://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}", data=data
            ) as resp:
                await resp.text()

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post_wrongpw(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {
                "token": "thiscantbetherealtokenorcanit",
                "match_name": "RCT with Lightwalker",
                "match_id": "1337",
            }
            async with session.post(
                f"https://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}", data=data
            ) as resp:
                await resp.text()


def setup(bot):
    bot.add_cog(Web(bot))
    bot.loop.create_task(web_server(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Web(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
