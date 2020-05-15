from datetime import datetime, timezone

import discord
from discord.ext import commands
import aiohttp

import core.perseverance
import core.config as config
from core.checks import in_whitelist


async def webhook_message(webhook_urls, message, username):
    async with aiohttp.ClientSession() as session:
        for webhook_url in webhook_urls:
            webhook = discord.Webhook.from_url(
                webhook_url, adapter=discord.AsyncWebhookAdapter(session)
            )
            await webhook.send(message, username=username)


async def webhook_embed(
    webhook_urls,
    title,
    description,
    fields,
    author_name,
    author_icon,
    username="RCTBot",
    avatar="https://i.imgur.com/Ou1k4lD.png",
    footer_text="Provided by RCTBot.",
    footer_icon="https://i.imgur.com/q8KmQtw.png",
):
    embed = discord.Embed(
        title=title,
        type="rich",
        description=description,
        color=0xFF6600,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(
        name=author_name,
        url=f"https://www.heroesofnewerth.com/playerstats/ranked/",
        icon_url=author_icon,
    )

    for field in fields:
        embed.add_field(
            name=field["name"], value=field["value"], inline=field["inline"]
        )

    embed.set_footer(
        text=footer_text, icon_url=footer_icon,
    )
    # embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
    async with aiohttp.ClientSession() as session:
        for webhook_url in webhook_urls:
            webhook = discord.Webhook.from_url(
                webhook_url, adapter=discord.AsyncWebhookAdapter(session)
            )
            await webhook.send(username=username, avatar_url=avatar, embed=embed)


class WebhookTesting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def wht(self, ctx, *, message: str):
        await webhook_message(
            config.DISCORD_LOG_WEBHOOKS, message, ctx.author.display_name
        )

    @commands.command()
    @in_whitelist(config.DISCORD_WHITELIST_IDS)
    async def whembed(self, ctx):
        fields = [
            {"name": "ft 1", "value": "fv 1", "inline": False},
            {"name": "ft 2", "value": "fv 2", "inline": True},
            {"name": "ft 3", "value": "fv 3", "inline": True},
        ]
        await webhook_embed(
            config.DISCORD_LOG_WEBHOOKS,
            "some title",
            "some desc",
            fields,
            ctx.author.display_name,
            ctx.author.avatar_url,
        )


def setup(bot):
    bot.add_cog(WebhookTesting(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
