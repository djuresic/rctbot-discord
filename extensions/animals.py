import aiohttp
import discord
from discord.ext import commands

import core.perseverance
import core.config as config


class Animals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cat(self, ctx):
        """Get a random cat image from The Cat API."""
        search_url = "https://api.thecatapi.com/v1/images/search"
        try:
            search_headers = {"x-api-key": config.CONFIG["CAT"]["x-api-key"]}
        except:
            search_headers = None

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=search_headers) as resp:
                json_resp = await resp.json()

        cat_dict = json_resp[0]
        cat_img_url = cat_dict["url"]

        await ctx.send(f"{cat_img_url}")

    @commands.command()
    async def dog(self, ctx):
        """Get a random dog image from The Dog API."""
        search_url = "https://api.thedogapi.com/v1/images/search"
        try:
            search_headers = {"x-api-key": config.CONFIG["DOG"]["x-api-key"]}
        except:
            search_headers = None

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=search_headers) as resp:
                json_resp = await resp.json()

        dog_dict = json_resp[0]
        dog_img_url = dog_dict["url"]

        await ctx.send(f"{dog_img_url}")


def setup(bot):
    bot.add_cog(Animals(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Animals(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
