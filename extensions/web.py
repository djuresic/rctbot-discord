import aiohttp
from aiohttp import web

import discord
from discord.ext import commands

import config
from extensions.checks import in_whitelist
from extensions.testing import game_hosted


async def web_server(bot):
    await bot.wait_until_ready()

    routes = web.RouteTableDef()

    @routes.get('/')
    async def hello_world(request):
        return web.Response(text=f"Hello, World! {config.WEB_DOMAIN} - OK")
    
    @routes.post(config.WEB_GAME_LOBBY_PATH)
    async def game_lobby(request): # POST handler for game lobbies
        try:
            token = (await request.post())['token']
        except:
            print(f"401: Unauthorized {config.WEB_GAME_LOBBY_PATH}")
            return web.Response(text="401: Unauthorized", status=401)

        if token != config.WEB_TOKEN:
            print(f"403: Forbidden {config.WEB_GAME_LOBBY_PATH}")
            return web.Response(text="403: Forbidden", status=403)

        try:
            # data = (await request.post())['data'] # This Soon(tm)
            # print(data)
            lobby_name = (await request.post())['match_name']
            match_id = (await request.post())['match_id']
            await game_hosted(bot, lobby_name, match_id)
            return web.Response(text="OK")
        except:
            return web.Response(text="400: Bad Request", status=400)
        #return web.Response(body='data: {}'.format(data))

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.WEB_LOCAL_IP, config.WEB_LOCAL_PORT)
    await site.start()
    print(f"Web server started on {config.WEB_LOCAL_IP}:{config.WEB_LOCAL_PORT} ({config.WEB_DOMAIN}).")


class Web(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {
                'token': config.WEB_TOKEN,
                'match_name': 'RCT with Lightwalker',
                'match_id': '1337'
            }
            async with session.post(f'https://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}', data=data) as resp:
                await resp.text()

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post_nopw(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {
                'match_name': 'RCT with Lightwalker',
                'match_id': '1337'
            }
            async with session.post(f'https://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}', data=data) as resp:
                await resp.text()

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def dev_post_wrongpw(self, ctx):
        async with aiohttp.ClientSession() as session:
            data = {
                'token': 'thiscantbetherealtokenorcanit',
                'match_name': 'RCT with Lightwalker',
                'match_id': '1337'
            }
            async with session.post(f'https://{config.WEB_DOMAIN}{config.WEB_GAME_LOBBY_PATH}', data=data) as resp:
                await resp.text()


def setup(bot):
    bot.add_cog(Web(bot))
    bot.loop.create_task(web_server(bot))
    config.BOT_LOADED_EXTENSIONS.append(__loader__.name)