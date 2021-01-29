from datetime import datetime, timezone

import aiohttp
import discord


async def webhook_message(webhook_urls, message, username):
    async with aiohttp.ClientSession() as session:
        for webhook_url in webhook_urls:
            webhook = discord.Webhook.from_url(webhook_url, adapter=discord.AsyncWebhookAdapter(session))
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
    color=0xFF6600,
):
    embed = discord.Embed(
        title=title, type="rich", description=description, color=color, timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(
        name=author_name, url=f"https://www.heroesofnewerth.com/playerstats/ranked/", icon_url=author_icon,
    )

    for field in fields:
        embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

    embed.set_footer(
        text=footer_text, icon_url=footer_icon,
    )
    # embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
    async with aiohttp.ClientSession() as session:
        for webhook_url in webhook_urls:
            webhook = discord.Webhook.from_url(webhook_url, adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(username=username, avatar_url=avatar, embed=embed)
