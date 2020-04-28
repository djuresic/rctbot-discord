import aiohttp


DEFAULT_AVATAR = "https://s3.amazonaws.com/naeu-icb2/icons/default/account/default.png"


async def get_avatar(account_id):
    "Fetch Custom Account Icon URL for Account ID."
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
