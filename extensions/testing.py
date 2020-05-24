import timeit
from collections import Counter
from time import strftime, gmtime

import aiohttp
import discord
from discord.ext import commands

import core.perseverance
import core.config as config
from core.checks import is_tester, is_senior, database_ready

from hon.masterserver import Client

# Move this to hon.res or hon.lists
ALL_HEROES = [
    "Accursed",
    "Adrenaline",
    "Aluna",
    "Amun-Ra",
    "Andromeda",
    "Apex",
    "Arachna",
    "Armadon",
    "Artesia",
    "Artillery",
    "Balphagore",
    "Behemoth",
    "Berzerker",
    "Blacksmith",
    "Blitz",
    "Blood Hunter",
    "Bombardier",
    "Bramble",
    "Bubbles",
    "Bushwack",
    "Calamity",
    "Chipper",
    "Chronos",
    "Circe",
    "Corrupted Disciple",
    "Cthulhuphant",
    "Dampeer",
    "Dark Lady",
    "Deadlift",
    "Deadwood",
    "Defiler",
    "Demented Shaman",
    "Devourer",
    "Doctor Repulsor",
    "Draconis",
    "Drunken Master",
    "Electrician",
    "Ellonia",
    "Emerald Warden",
    "Empath",
    "Engineer",
    "Fayde",
    "Flint Beastwood",
    "Flux",
    "Forsaken Archer",
    "Gauntlet",
    "Gemini",
    "Genesis",
    "Geomancer",
    "Glacius",
    "Gladiator",
    "Goldenveil",
    "Gravekeeper",
    "Grinex",
    "Gunblade",
    "Hammerstorm",
    "Hellbringer",
    "Ichor",
    "Jeraziah",
    "Kane",
    "Keeper of the Forest",
    "Kinesis",
    "King Klout",
    "Klanx",
    "Kraken",
    "Legionnaire",
    "Lodestone",
    "Lord Salforis",
    "Madman",
    "Magebane",
    "Magmus",
    "Maliken",
    "Martyr",
    "Master of Arms",
    "Midas",
    "Moira",
    "Monarch",
    "Monkey King",
    "Moon Queen",
    "Moraxus",
    "Myrmidon",
    "Night Hound",
    "Nitro",
    "Nomad",
    "Nymphora",
    "Oogie",
    "Ophelia",
    "Pandamonium",
    "Parallax",
    "Parasite",
    "Pearl",
    "Pebbles",
    "Pestilence",
    "Pharaoh",
    "Plague Rider",
    "Pollywog Priest",
    "Predator",
    "Prisoner 945",
    "Prophet",
    "Puppet Master",
    "Pyromancer",
    "Qi",
    "Rally",
    "Rampage",
    "Ravenor",
    "Revenant",
    "Rhapsody",
    "Riftwalker",
    "Riptide",
    "Salomon",
    "Sand Wraith",
    "Sapphire",
    "Scout",
    "Shadowblade",
    "Shellshock",
    "Silhouette",
    "Sir Benzington",
    "Skrap",
    "Slither",
    "Solstice",
    "Soul Reaper",
    "Soulstealer",
    "Succubus",
    "Swiftblade",
    "Tarot",
    "Tempest",
    "Thunderbringer",
    "Torturer",
    "Tremble",
    "Tundra",
    "Valkyrie",
    "Vindicator",
    "Voodoo Jester",
    "War Beast",
    "Warchief",
    "Wildsoul",
    "Witch Slayer",
    "Wretched Hag",
    "Zephyr",
    "Accursed",
    "Adrenaline",
    "Aluna",
    "Amun-Ra",
    "Andromeda",
    "Apex",
    "Arachna",
    "Armadon",
    "Artesia",
    "Artillery",
    "Balphagore",
    "Behemoth",
    "Berzerker",
    "Blacksmith",
    "Blitz",
    "Blood Hunter",
    "Bombardier",
    "Bramble",
    "Bubbles",
    "Bushwack",
    "Calamity",
    "Chi",
    "Chipper",
    "Chronos",
    "Circe",
    "Corrupted Disciple",
    "Cthulhuphant",
    "Dampeer",
    "Dark Lady",
    "Deadlift",
    "Deadwood",
    "Defiler",
    "Demented Shaman",
    "Devourer",
    "Doctor Repulsor",
    "Draconis",
    "Drunken Master",
    "Electrician",
    "Ellonia",
    "Emerald Warden",
    "Empath",
    "Engineer",
    "Fayde",
    "Flint Beastwood",
    "Flux",
    "Forsaken Archer",
    "Gauntlet",
    "Gemini",
    "Genesis",
    "Geomancer",
    "Glacius",
    "Gladiator",
    "Goldenveil",
    "Gravekeeper",
    "Grinex",
    "Gunblade",
    "Hammerstorm",
    "Hellbringer",
    "Ichor",
    "Jeraziah",
    "Kane",
    "Keeper of the Forest",
    "Kinesis",
    "King Klout",
    "Klanx",
    "Kraken",
    "Legionnaire",
    "Lodestone",
    "Lord Salforis",
    "Madman",
    "Magebane",
    "Magmus",
    "Maliken",
    "Martyr",
    "Master of Arms",
    "Midas",
    "Mimix",
    "Moira",
    "Monarch",
    "Monkey King",
    "Moon Queen",
    "Moraxus",
    "Myrmidon",
    "Night Hound",
    "Nitro",
    "Nomad",
    "Nymphora",
    "Oogie",
    "Ophelia",
    "Pandamonium",
    "Parallax",
    "Parasite",
    "Pearl",
    "Pebbles",
    "Pestilence",
    "Pharaoh",
    "Plague Rider",
    "Pollywog Priest",
    "Predator",
    "Prisoner 945",
    "Prophet",
    "Puppet Master",
    "Pyromancer",
    "Rally",
    "Rampage",
    "Ravenor",
    "Revenant",
    "Rhapsody",
    "Riftwalker",
    "Riptide",
    "Salomon",
    "Sand Wraith",
    "Sapphire",
    "Scout",
    "Shadowblade",
    "Shellshock",
    "Silhouette",
    "Sir Benzington",
    "Skrap",
    "Slither",
    "Solstice",
    "Soul Reaper",
    "Soulstealer",
    "Succubus",
    "Swiftblade",
    "Tarot",
    "Tempest",
    "Thunderbringer",
    "Torturer",
    "Tremble",
    "Tundra",
    "Valkyrie",
    "Vindicator",
    "Voodoo Jester",
    "War Beast",
    "Warchief",
    "Wildsoul",
    "Witch Slayer",
    "Wretched Hag",
    "Xemplar",
    "Zephyr",
    "Catman Champion",
    "Dragon Master",
    "Dreadbeetle Queen",
    "Minotaur",
    "Predasaur Crusher",
    "Skeleton King",
    "Vulture Lord",
    "Vagabond Leader",
    "Werebeast Enchanter",
    "Wolf Commander",
    "Dragon",
]
ALL_ITEMS = [
    "Abyssal Skull",
    "Acolyte's Staff",
    "Alacrity Band",
    "Alchemist's Bones",
    "Amulet of Exile",
    "Apprentice's Robe",
    "Arcana",
    "Arcane Bomb",
    "Arcane Nullifier",
    "Armor of the Mad Mage",
    "Assassin's Shroud",
    "Astrolabe",
    "Axe of the Malphai",
    "Barbed Armor",
    "Barrier Idol",
    "Beastheart",
    "Behemoth's Heart",
    "Blessed Orb",
    "Blight Stones",
    "Blood Chalice",
    "Bloodborne Maul",
    "Bolstering Armband",
    "Bottle",
    "Bound Eye",
    "Broadsword",
    "Brutalizer",
    "Codex",
    "Corrupted Sword",
    "Crushing Claws",
    "Daemonic Breastplate",
    "Dancing Blade",
    "Dawnbringer",
    "Doom Bringer",
    "Dreamcatcher",
    "Duck Boots",
    "Dust of Revelation",
    "Elder Parasite",
    "Energizer",
    "Firebrand",
    "Fleetfeet",
    "Flying Courier",
    "Fortified Bracer",
    "Frostburn",
    "Frostwolf's Skull",
    "Frozen Light",
    "Genjuro",
    "Geometer's Bane",
    "Ghost Marchers",
    "Gloves of the Swift",
    "Glowstone",
    "Grave Locket",
    "Grimoire of Power",
    "Guardian Ring",
    "Harkon's Blade",
    "Health Potion",
    "Hellflower",
    "Helm of the Black Legion",
    "Helm of the Victim",
    "Homecoming Stone",
    "Hungry Spirit",
    "Hypercrown",
    "Icebrand",
    "Icon of the Goddess",
    "Insanitarius",
    "Iron Buckler",
    "Iron Shield",
    "Jade Spire",
    "Kuldra's Sheepstick",
    "Lex Talionis",
    "Lifetube",
    "Lightbrand",
    "Logger's Hatchet",
    "Luminous Prism",
    "Madfred's Brass Knuckles",
    "Major Totem",
    "Mana Potion",
    "Manatube",
    "Marchers",
    "Mark of the Novice",
    "Master's Legacy",
    "Mighty Blade",
    "Minor Totem",
    "Mock of Brilliance",
    "Mystic Vestments",
    "Neophyte's Book",
    "Nome's Wisdom",
    "Null Stone",
    "Nullfire Blade",
    "Ophelia's Pact",
    "Orb of Zamos",
    "Perpetual Cogwheel",
    "Pickled Brain",
    "Plated Greaves",
    "Platemail",
    "Portal Key",
    "Post Haste",
    "Power Supply",
    "Pretender's Crown",
    "Punchdagger",
    "Puzzlebox",
    "Quickblade",
    "Refreshing Ornament",
    "Rejuvenation Potion",
    "Restoration Stone",
    "Riftshards",
    "Ring of Sorcery",
    "Ring of the Teacher",
    "Ringmail",
    "Runed Cleaver",
    "Sand Scepter",
    "Savage Mace",
    "Scarab",
    "Searing Light",
    "Shaman's Headdress",
    "Shield of the Five",
    "Shieldbreaker",
    "Shrunken Head",
    "Slayer",
    "Snake Bracelet",
    "Sol's Bulwark",
    "Sorcery Boots",
    "Soulscream Ring",
    "Soultrap",
    "Spell Sunder",
    "Spellshards",
    "Spiked Bola",
    "Staff of the Master",
    "Steamboots",
    "Steamstaff",
    "Stormspirit",
    "Striders",
    "Sustainer",
    "Sword of the High",
    "Symbol of Rage",
    "Tablet of Command",
    "Thunderclaw",
    "Trinket of Restoration",
    "Twin Blades",
    "Ultor's Heavy Helm",
    "Veiled Rot",
    "Void Talisman",
    "Void Talisman",
    "Voltstone",
    "Ward of Revelation",
    "Ward of Sight",
    "Warhammer",
    "Warpcleft",
    "Whispering Helm",
    "Wind Whistle",
    "Wingbow",
    "Tome of Elements",
    "Ioyn Stone",
    "Toxin Claws",
    "Sacrificial Stone",
    "Token of Life",
    "Frostfield Plate",
]


async def game_hosted(bot, match_name, match_id):
    channel = bot.get_channel(config.DISCORD_GAME_LOBBIES_CHANNEL_ID)
    return await channel.send(
        f"Game **{match_name}** ({match_id}) has been created. **Join up!**"
    )


async def cc_detected(bot, nickname, account_id):
    channel = bot.get_channel(config.DISCORD_BOT_LOG_CHANNEL_ID)
    return await channel.send(
        f"Player **{nickname}** ({account_id}) should not be wearing the Mentor Wings chat color!"
    )


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_tester()
    async def notes(self, ctx):
        """Returns current testing notes"""
        author = ctx.author
        log_channel = self.bot.get_channel(config.DISCORD_NOTES_CHANNEL_ID)

        token_generator = f"https://{config.HON_ALT_DOMAIN}/site/create-access-token"
        cat_query = {"discordId": author.id, "password": config.HON_CAT_PASSWORD}

        async with aiohttp.ClientSession() as session:

            async with session.get(token_generator, params=cat_query) as resp:
                token = await resp.text()

        notes_url = f"https://{config.HON_ALT_DOMAIN}/{token}"
        await author.send(f"Current Testing Notes: {notes_url}")
        await log_channel.send(
            f'({strftime("%a, %d %b %Y, %H:%M:%S %Z", gmtime())}) {author.mention} received Testing Notes with the URL: `{notes_url}`'
        )

    @commands.command()
    @is_tester()
    async def version(self, ctx, masterserver: str = "rc"):
        """Check all client versions for <masterserver>. Defaults to RCT masterserver."""

        async with ctx.message.channel.typing():

            async with aiohttp.ClientSession() as session:
                ms = Client(masterserver, session=session)
                w_version = await ms.latest_client_version("windows")
                m_version = await ms.latest_client_version("mac")
                l_version = await ms.latest_client_version("linux")

            embed = discord.Embed(
                title=ms.client_name,
                type="rich",
                description="Client Version",
                color=ms.color,
                timestamp=ctx.message.created_at,
            )
            embed.set_author(
                name=ctx.author.display_name, icon_url=ctx.author.avatar_url
            )
            embed.add_field(name="Windows", value=w_version, inline=True)
            embed.add_field(name="macOS", value=m_version, inline=True)
            embed.add_field(name="Linux", value=l_version, inline=True)
            embed.set_footer(
                text="Yes honey.", icon_url="https://i.imgur.com/q8KmQtw.png",
            )

            await ctx.send(embed=embed)

    @commands.command(aliases=["changed"])
    @is_senior()
    async def changes(self, ctx):
        token_generator = f"https://{config.HON_ALT_DOMAIN}/site/create-access-token"
        cat_query = {"discordId": self.bot.user.id, "password": config.HON_CAT_PASSWORD}

        async with aiohttp.ClientSession() as session:

            async with session.get(token_generator, params=cat_query) as resp:
                token = await resp.text()

            notes_url = f"https://{config.HON_ALT_DOMAIN}/{token}"

            async with session.get(notes_url) as resp:
                notes = await resp.text()

            changed_heroes = []
            for hero in ALL_HEROES:
                if hero in notes and hero not in changed_heroes:
                    changed_heroes.append(hero)

            if "Chi" in changed_heroes:
                changed_heroes.remove("Chi")

            changed_items = []
            for item in ALL_ITEMS:
                if item in notes and item not in changed_items:
                    changed_items.append(item)

            await ctx.send(
                "**{}**{}\n\n**Changed heroes:** {}\n\n**Changed items:** {}".format(
                    notes.split("<br />")[0][:-2],
                    notes.split("<br />")[2],
                    ", ".join(sorted(changed_heroes)),
                    ", ".join(sorted(changed_items)),
                )
            )

    # TO DO: this needs to be prettier
    @commands.command(aliases=["hero", "herousage"])
    @is_senior()
    @database_ready()
    async def usage(self, ctx):
        """Hero usage list for the current patch cycle."""
        hul_embed = discord.Embed(title="Hero Usage List", type="rich", color=0xFF6600)
        hul_embed.set_author(
            name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url
        )
        hul_embed.add_field(name="By Hero", value="📈")
        hul_embed.add_field(name="By Player", value="📉")
        hul_embed.add_field(name="Show All Picks", value="📊")
        hul_embed.add_field(name="Not Picked", value="❗")
        hul_embed.set_footer(text="Please add one of the reactions above to continue.")
        hul_message = await ctx.send(embed=hul_embed)
        # await asyncio.sleep(0.1)
        await hul_message.add_reaction("📈")
        await hul_message.add_reaction("📉")
        await hul_message.add_reaction("📊")
        await hul_message.add_reaction("❗")
        reaction, _ = await self.bot.wait_for(
            "reaction_add",
            check=lambda reaction, user: user == ctx.message.author
            and reaction.emoji in ["📈", "📉", "📊", "❗"]
            and reaction.message.id == hul_message.id,
        )
        # reaction_action=await self.bot.wait_for_reaction(['📈','📉','📊'], user=ctx.message.author, timeout=60.0, message=hul_message)
        await hul_message.delete()
        try:
            if reaction.emoji == "📊":
                heroes = []
                try:
                    for x in config.PLAYER_SLASH_HERO:
                        if x != "" and "/" in x:
                            y = x.split(",")
                            for z in y:
                                k = z.split("/")[1]
                                heroes.append(k)
                except:
                    await ctx.send("Unavailable. Please wait for the next conversion.")
                    return

                hero_counter = Counter(heroes)
                hero_keys = hero_counter.keys()
                hero_values = hero_counter.values()

                hero_percent = []
                hero_no_percent = []
                last_hero = []
                discord_message = []

                for val in hero_values:
                    hero_percent.append(round((int(val) * 100) / len(heroes), 2))
                    hero_no_percent.append(int(val))
                for hero in hero_keys:
                    last_hero.append(hero)
                for percent in range(0, len(hero_percent), 1):
                    discord_message.append(
                        "\n{0}: **{1}** ({2}%)".format(
                            last_hero[percent],
                            hero_no_percent[percent],
                            hero_percent[percent],
                        )
                    )

                discord_message.sort()

                length = len(hero_percent)
                if length <= 50:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:length]))
                elif length <= 100:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:length]))
                elif length <= 150:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:100]))
                    await ctx.send("".join(discord_message[100:length]))
                else:
                    await ctx.send(
                        "Unique hero picks: **{0}**\nDifferent heroes picked: **{1}**".format(
                            len(heroes), length
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:100]))
                    await ctx.send("".join(discord_message[100:150]))
                    await ctx.send("".join(discord_message[150:length]))

            elif reaction.emoji == "📈":
                heroes = []
                players = []
                try:
                    for x in config.PLAYER_SLASH_HERO:
                        if x != "" and "/" in x:
                            y = x.split(",")
                            for z in y:
                                h = z.split("/")[0]
                                h = h.strip(" ")
                                k = z.split("/")[1]
                                heroes.append(k)
                                players.append(h)
                except:
                    await ctx.send("Please convert to proper format first.")
                    return
                await ctx.send("Please enter the name of the hero:")
                wf_message = await self.bot.wait_for(
                    "message", check=lambda m: m.author == ctx.message.author
                )
                hero_name = wf_message.content
                hero_name_lower = hero_name.lower()
                try:
                    [x.lower() for x in heroes].index(hero_name_lower)
                except:
                    await ctx.send(
                        "**{0}** was not picked this cycle.".format(hero_name.title())
                    )
                    return
                hero_counter = 0
                for i in heroes:
                    if i == hero_name:
                        hero_counter += 1
                # heroPercentage=((hero_counter*100)/len(heroes))
                played_by = []
                for i in range(0, len(heroes), 1):
                    if heroes[i].lower() == hero_name_lower:
                        played_by.append(players[i])
                        hero_name = heroes[i]
                played_by = Counter(played_by)
                nb_plays = played_by.values()
                nb_plays_c = []
                for i in nb_plays:
                    nb_plays_c.append(str(i))
                played_by = played_by.keys()
                played_by_o = []
                for i in played_by:
                    played_by_o.append(i)
                discord_message = []
                for i in range(0, len(played_by_o)):
                    if i == (len(played_by_o) - 1):
                        temp = (
                            "\n"
                            + discord.utils.escape_markdown(played_by_o[i])
                            + ": **"
                            + nb_plays_c[i]
                            + "**"
                        )
                        discord_message.append(temp)
                    else:
                        temp = (
                            "\n"
                            + discord.utils.escape_markdown(played_by_o[i])
                            + ": **"
                            + nb_plays_c[i]
                            + "**"
                        )
                        discord_message.append(temp)
                discord_message.sort()
                length = len(discord_message)
                if length <= 50:
                    await ctx.send("**{0}** was picked by:".format(hero_name))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:length]))
                elif length <= 100:
                    await ctx.send("**{0}** was picked by:".format(hero_name))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:length]))
                else:
                    await ctx.send("**{0}** was picked by:".format(hero_name))
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(discord_message[0:50]))
                    await ctx.send("".join(discord_message[50:100]))
                    await ctx.send("".join(discord_message[100:length]))
            elif reaction.emoji == "📉":
                heroes = []
                players = []
                try:
                    for x in config.PLAYER_SLASH_HERO:
                        if x != "" and "/" in x:
                            y = x.split(",")
                            for z in y:
                                h = z.split("/")[0]
                                h = h.strip(" ")
                                k = z.split("/")[1]
                                heroes.append(k)
                                players.append(h)
                except Exception:
                    await ctx.send("Please convert to proper format first.")
                    return
                await ctx.send("Please enter the name of the player:")
                wf_message = await self.bot.wait_for(
                    "message", check=lambda m: m.author == ctx.message.author
                )
                playerName = wf_message.content
                playerNameLower = playerName.lower()
                try:
                    [x.lower() for x in players].index(playerNameLower)
                except:
                    await ctx.send(
                        "**{0}** did not play this cycle.".format(playerName)
                    )
                    return
                playedHeroes = []
                for i in range(0, len(players)):
                    if players[i].lower() == playerNameLower:
                        playedHeroes.append(heroes[i])
                        playerName = players[i]
                playedHeroes = Counter(playedHeroes)
                heroesNames = playedHeroes.keys()
                heroesCount = playedHeroes.values()
                hero_name = []
                heroCount = []
                for i in heroesNames:
                    hero_name.append(i)
                for i in heroesCount:
                    heroCount.append(str(i))
                lastHero = []
                for i in range(0, len(hero_name)):
                    if i == (len(hero_name) - 1):
                        temp = "\n" + hero_name[i] + ": **" + heroCount[i] + "**"
                        lastHero.append(temp)
                    else:
                        temp = "\n" + hero_name[i] + ": **" + heroCount[i] + "**"
                        lastHero.append(temp)
                lastHero.sort()
                length = len(lastHero)
                if length <= 50:
                    await ctx.send(
                        "Hero picks for **{0}**:".format(
                            discord.utils.escape_markdown(playerName)
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(lastHero[0:length]))
                elif length <= 100:
                    await ctx.send(
                        "Hero picks for **{0}**:".format(
                            discord.utils.escape_markdown(playerName)
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(lastHero[0:50]))
                    await ctx.send("".join(lastHero[50:length]))
                else:
                    await ctx.send(
                        "Hero picks for **{0}**:".format(
                            discord.utils.escape_markdown(playerName)
                        )
                    )
                    # await asyncio.sleep(0.25)
                    await ctx.send("".join(lastHero[0:50]))
                    await ctx.send("".join(lastHero[50:100]))
                    await ctx.send("".join(lastHero[100:length]))

            elif reaction.emoji == "❗":
                token_generator = (
                    f"https://{config.HON_ALT_DOMAIN}/site/create-access-token"
                )
                cat_query = {
                    "discordId": self.bot.user.id,
                    "password": config.HON_CAT_PASSWORD,
                }

                async with aiohttp.ClientSession() as session:

                    async with session.get(token_generator, params=cat_query) as resp:
                        token = await resp.text()

                    notes_url = f"https://{config.HON_ALT_DOMAIN}/{token}"

                    async with session.get(notes_url) as resp:
                        notes = await resp.text()

                    changed_heroes = []
                    for hero in ALL_HEROES:
                        if hero in notes and hero not in changed_heroes:
                            changed_heroes.append(hero)

                    heroes = []
                    try:
                        for x in config.PLAYER_SLASH_HERO:
                            if x != "" and "/" in x:
                                y = x.split(",")
                                for z in y:
                                    k = z.split("/")[1]
                                    heroes.append(k)
                    except:
                        await ctx.send(
                            "Unavailable. Please wait for the next conversion."
                        )
                        return

                    picked_heroes = [
                        hero.lower() for hero in list(Counter(heroes).keys())
                    ]
                    not_picked = []
                    for hero in changed_heroes:
                        if hero.lower() not in picked_heroes:
                            not_picked.append(hero)

                    if "Chi" in not_picked:
                        not_picked.remove("Chi")

                    await ctx.send(
                        "The following **{}** heroes were not picked this cycle:\n**{}**".format(
                            len(not_picked), "\n".join(sorted(not_picked))
                        )
                    )
        except Exception:
            return

    @commands.command()
    @is_senior()
    async def notpicked(self, ctx):
        token_generator = f"https://{config.HON_ALT_DOMAIN}/site/create-access-token"
        cat_query = {"discordId": self.bot.user.id, "password": config.HON_CAT_PASSWORD}

        async with aiohttp.ClientSession() as session:

            async with session.get(token_generator, params=cat_query) as resp:
                token = await resp.text()

            notes_url = f"https://{config.HON_ALT_DOMAIN}/{token}"

            async with session.get(notes_url) as resp:
                notes = await resp.text()

            changed_heroes = []
            for hero in ALL_HEROES:
                if hero in notes and hero not in changed_heroes:
                    changed_heroes.append(hero)

            heroes = []
            try:
                for x in config.PLAYER_SLASH_HERO:
                    if x != "" and "/" in x:
                        y = x.split(",")
                        for z in y:
                            k = z.split("/")[1]
                            heroes.append(k)
            except:
                await ctx.send("Unavailable. Please wait for the next conversion.")
                return

            picked_heroes = [hero.lower() for hero in list(Counter(heroes).keys())]
            not_picked = []
            for hero in changed_heroes:
                if hero.lower() not in picked_heroes:
                    not_picked.append(hero)

            if "Chi" in not_picked:
                not_picked.remove("Chi")

            await ctx.send(
                "The following {} heroes were not picked this cycle:\n{}".format(
                    len(not_picked), "\n".join(sorted(not_picked))
                )
            )


def setup(bot):
    bot.add_cog(Testing(bot))
    core.perseverance.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(Testing(bot))
    core.perseverance.LOADED_EXTENSIONS.remove(__loader__.name)
