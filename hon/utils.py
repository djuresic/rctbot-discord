"""HoN utilites"""

import aiohttp

import config


DEFAULT_AVATAR = "https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png"
CHAT_COLORS = {
    "frostburnlogo": 0xFF0000,
    "gmgold": 0xDD0040,
    "gmshield": 0xDD0040,
    "banhammer": 0xDD0040,
    "techtinker": 0xDD0040,
    "mentorwings": 0xFF6600,
    "sbtsenior": 0x775033,
    "sbtpremium": 0x0059FF,
    "sbteye": 0x0059FF,
    "championofnewerth": 0x6F22B6,
    "limesoda": 0x66FF99,
    "darkwitch": 0xDE33FF,
    "darkpinkrose": 0xFF1493,
    "pixelpower": 0x00C0FF,
    "jackpot": 0xFFFF33,
    "surpriseworldgingerbread": 0xFF0000,
    "darkbloodyhalloween": 0xFF3000,
    "candycane": 0xFF0000,
    "strawberrybananacake": 0xFF6699,
    "sweetmeat": 0xFFCCFF,  # This one could be changed.
    "punkpower": 0xFFD200,
    "naughtymisfit": 0xA0C063,
    "docileplushie": 0xFF3D8F,
    "highroller": 0xFBFF0C,
    "cybercolor": 0xF8732C,
    "paragonglow": 0x00CEFF,
    "gcacolor": 0xFFBA00,
    "soulharvest": 0xFF6C00,
    "mudblood": 0xFF1A33,
    "glowinggold": 0xCD9B1D,
    "glowingpink": 0xFF007F,
    "glowingursa": 0xD1F500,
    "glowinghalloween": 0xF8732C,
    "frostfieldssilver": 0xD3DDEB,
    "stardustgreen": 0x42F02A,
    "glowingwater": 0x4BFCFC,
    "aquamarine": 0x00FDB2,
    "emerald": 0x1CFC2F,
    "tanzanite": 0x863EF0,
    "pink": 0xFC65A5,
    "diamond": 0x2AC1FA,
    "goldshield": 0xDBBF4A,
    "silvershield": 0x7C8DA7,
    "white": 0xFFFFFF,
}
HERO_NAMES = {
    "Hero_Mimix": "Xemplar",
    "Hero_Oogie": "Oogie",
    "Hero_DiseasedRider": "Plague Rider",
    "Hero_Nomad": "Nomad",
    "Hero_Ellonia": "Ellonia",
    "Hero_Rally": "Rally",
    "Hero_PollywogPriest": "Pollywog Priest",
    "Hero_Riptide": "Riptide",
    "Hero_Parasite": "Parasite",
    "Hero_Hiro": "Swiftblade",
    "Hero_SirBenzington": "Sir Benzington",
    "Hero_Andromeda": "Andromeda",
    "Hero_Bombardier": "Bombardier",
    "Hero_Prisoner": "Prisoner 945",
    "Hero_KingKlout": "King Klout",
    "Hero_Aluna": "Aluna",
    "Hero_Bushwack": "Bushwack",
    "Hero_Ophelia": "Ophelia",
    "Hero_Solstice": "Solstice",
    "Hero_Ra": "Amun-Ra",
    "Hero_ForsakenArcher": "Forsaken Archer",
    "Hero_Ichor": "Ichor",
    "Hero_Gemini": "Gemini",
    "Hero_Martyr": "Martyr",
    "Hero_Electrician": "Electrician",
    "Hero_Shaman": "Demented Shaman",
    "Hero_Treant": "Keeper of the Forest",
    "Hero_Accursed": "Accursed",
    "Hero_Cthulhuphant": "Cthulhuphant",
    "Hero_Voodoo": "Voodoo Jester",
    "Hero_Tempest": "Tempest",
    "Hero_CorruptedDisciple": "Corrupted Disciple",
    "Hero_Arachna": "Arachna",
    "Hero_Armadon": "Armadon",
    "Hero_Hammerstorm": "Hammerstorm",
    "Hero_FlintBeastwood": "Flint Beastwood",
    "Hero_Tremble": "Tremble",
    "Hero_Hellbringer": "Hellbringer",
    "Hero_Ebulus": "Slither",
    "Hero_Tarot": "Tarot",
    "Hero_Warchief": "Warchief",
    "Hero_Krixi": "Moon Queen",
    "Hero_Revenant": "Revenant",
    "Hero_Xalynx": "Torturer",
    "Hero_Nitro": "Nitro",
    "Hero_HellDemon": "Soul Reaper",
    "Hero_Bubbles": "Bubbles",
    "Hero_Hydromancer": "Myrmidon",
    "Hero_Frosty": "Glacius",
    "Hero_Maliken": "Maliken",
    "Hero_Fade": "Fayde",
    "Hero_ShadowBlade": "Shadowblade",
    "Hero_Fairy": "Nymphora",
    "Hero_WolfMan": "War Beast",
    "Hero_Rocky": "Pebbles",
    "Hero_Rhapsody": "Rhapsody",
    "Hero_Defiler": "Defiler",
    "Hero_Silhouette": "Silhouette",
    "Hero_Midas": "Midas",
    "Hero_Gladiator": "The Gladiator",
    "Hero_DoctorRepulsor": "Doctor Repulsor",
    "Hero_Moira": "Moira",
    "Hero_MasterOfArms": "Master Of Arms",
    "Hero_Empath": "Empath",
    "Hero_Apex": "Apex",
    "Hero_Deadlift": "Deadlift",
    "Hero_Sapphire": "Sapphire",
    "Hero_Devourer": "Devourer",
    "Hero_Berzerker": "Berzerker",
    "Hero_SandWraith": "Sand Wraith",
    "Hero_Blitz": "Blitz",
    "Hero_FlameDragon": "Draconis",
    "Hero_Yogi": "Wildsoul",
    "Hero_Pestilence": "Pestilence",
    "Hero_Kenisis": "Kinesis",
    "Hero_Grinex": "Grinex",
    "Hero_WitchSlayer": "Witch Slayer",
    "Hero_Javaras": "Magebane",
    "Hero_Artesia": "Artesia",
    "Hero_Engineer": "Engineer",
    "Hero_PuppetMaster": "Puppet Master",
    "Hero_Salomon": "Salomon",
    "Hero_Parallax": "Parallax",
    "Hero_DwarfMagi": "Blacksmith",
    "Hero_Chi": "Qi",
    "Hero_Kane": "Kane",
    "Hero_Klanx": "Klanx",
    "Hero_Kraken": "Kraken",
    "Hero_Circe": "Circe",
    "Hero_EmeraldWarden": "Emerald Warden",
    "Hero_Mumra": "Pharaoh",
    "Hero_Chipper": "The Chipper",
    "Hero_Deadwood": "Deadwood",
    "Hero_Soulstealer": "Soulstealer",
    "Hero_Hantumon": "Night Hound",
    "Hero_Chronos": "Chronos",
    "Hero_Vanya": "The Dark Lady",
    "Hero_Bephelgor": "Balphagore",
    "Hero_Plant": "Bramble",
    "Hero_Flux": "Flux",
    "Hero_Shellshock": "Shellshock",
    "Hero_Moraxus": "Moraxus",
    "Hero_Pyromancer": "Pyromancer",
    "Hero_Valkyrie": "Valkyrie",
    "Hero_Legionnaire": "Legionnaire",
    "Hero_Scout": "Scout",
    "Hero_Artillery": "Artillery",
    "Hero_PyromancerTutorial": "Pyromancer",
    "Hero_Lodestone": "Lodestone",
    "Hero_Monarch": "Monarch",
    "Hero_Dreadknight": "Lord Salforis",
    "Hero_Genesis": "Genesis",
    "Hero_Hunter": "Blood Hunter",
    "Hero_Prophet": "Prophet",
    "Hero_Goldenveil": "Goldenveil",
    "Hero_Kunas": "Thunderbringer",
    "Hero_Taint": "Gravekeeper",
    "Hero_Rampage": "Rampage",
    "Hero_Gauntlet": "Gauntlet",
    "Hero_Adrenaline": "Adrenaline",
    "Hero_Behemoth": "Behemoth",
    "Hero_Vindicator": "Vindicator",
    "Hero_Dampeer": "Dampeer",
    "Hero_Tundra": "Tundra",
    "Hero_Scar": "The Madman",
    "Hero_Calamity": "Calamity",
    "Hero_Succubis": "Succubus",
    "Hero_Jereziah": "Jeraziah",
    "Hero_MonkeyKing": "Monkey King",
    "Hero_Skrap": "Skrap",
    "Hero_Geomancer": "Geomancer",
    "Hero_Pearl": "Pearl",
    "Hero_Ravenor": "Ravenor",
    "Hero_BabaYaga": "Wretched Hag",
    "Hero_Predator": "Predator",
    "Hero_Riftmage": "Riftwalker",
    "Hero_DrunkenMaster": "Drunken Master",
    "Hero_Magmar": "Magmus",
    "Hero_Gunblade": "Gunblade",
    "Hero_Zephyr": "Zephyr",
    "Hero_Panda": "Pandamonium",
}


async def get_avatar(account_id):
    """Fetch Custom Account Icon URL for Account ID."""
    url = "http://www.heroesofnewerth.com/getAvatar_SSL.php"
    query = {"id": account_id}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=query, allow_redirects=False) as resp:
                location = resp.headers["Location"]
                if not location.endswith(".cai"):
                    return DEFAULT_AVATAR
                elif "icons//" in location:
                    return location.replace("icons//", "icons/")
                else:
                    return DEFAULT_AVATAR
        except:
            return DEFAULT_AVATAR


async def get_name_color(masterserver_response):
    """Return Chat (Name) Color as a hexadecimal integer from masterserever response
    which contains Chat Color information in selected_upgrades."""
    selected_upgrades = [
        v.decode()
        for v in masterserver_response[b"selected_upgrades"].values()
        if isinstance(v, bytes)
    ]

    color = None
    for upgrade in selected_upgrades:
        if upgrade.startswith("cc."):
            color = upgrade[3:]
            break
    if color is not None and color in CHAT_COLORS:
        return CHAT_COLORS[color]
    else:
        return 0xFFFFFF


async def hero_name(cli_name):
    """Return official hero name."""
    if cli_name in HERO_NAMES:
        return HERO_NAMES[cli_name]
    else:
        return "Unknown"


# pylint: disable=unused-argument
def setup(bot):
    config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    config.LOADED_EXTENSIONS.remove(__loader__.name)
