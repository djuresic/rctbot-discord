from __future__ import annotations

import asyncio
from typing import Tuple

import aiohttp
import discord
from discord.ext import commands, tasks

import rctbot.config
from rctbot.core import checks
from rctbot.core.driver import AsyncDatabaseHandler


class EmbedCreator:
    def __init__(self, ctx: commands.Context) -> None:
        self.ctx = ctx

    async def rules(self) -> Tuple[discord.Embed, discord.Embed]:
        mod_mention = discord.utils.get(self.ctx.guild.roles, name="Discord Moderator").mention
        off_topic = discord.utils.get(self.ctx.guild.channels, name="off-topic").mention
        stream_promo = discord.utils.get(self.ctx.guild.channels, name="stream-promotions").mention
        description = (
            "As the official Heroes of Newerth Discord server, we adhere to and enforce the terms of service and code"
            " of conduct, along with all community guidelines set forth by Frostburn Studios and Discord, including"
            " but not limited to"
            " [Heroes of Newerth Account Terms of Service](https://www.heroesofnewerth.com/documents/tos/),"
            " [Heroes of Newerth Player Code of Conduct](http://www.heroesofnewerth.com/documents/conduct),"
            " [Discord Terms of Service](https://discord.com/terms),"
            " and [Discord Community Guidelines](https://discord.com/guidelines)."
            " Members must also comply with all applicable laws. Failure to abide by any of the aforementioned"
            " or following rules will lead to punishment based on the severity of the offense."
            " Thank you for helping us build a better, healthier community!"
        )
        no_pings_title = "Do not ping staff or abuse Discord mentions."
        no_pings_desc = (
            "Do not mention or DM inactive members who aren't part of the present conversation, especially"
            " Frostburn and Garena employees. Violations may lead to anything from simple mutes to permanent bans"
            " if done consecutively and to purposefully break this rule. This doesn't apply if you're mentioning"
            " someone with whom you have some kind of mutual relationship."
        )
        be_polite_title = "Be polite and use common sense."
        be_polite_desc = (
            "No harassment, hate speech, racism, sexism, ableism, trolling, stereotype based attacks, or spreading"
            " harmful/false information. Do not stir up drama. If there is a conflict, work to defuse it instead of"
            ' making it worse. Use of slurs or any "substitutes", especially in a disparaging manner (such as calling'
            ' someone or something "gay" with a negative implication), will not be tolerated. You may be banned'
            " immediately and without warning or recourse."
        )
        no_nsfw_content_title = "No NSFW or inappropriate content."
        no_nsfw_content_desc = (
            "Do not post anything that is NSFW or generally inappropriate. This includes shocking, gory, lewd, erotic,"
            " or otherwise NSFW content, as well as statements with an underlying NSFW tone. If you are unsure whether"
            " something is considered NSFW, you shouldn't post it. Violation of this rule may be cause for an"
            " immediate ban and the offending message reported to Discord's Trust and Safety team."
        )
        channel_purpose_title = "Use channels for their purpose."
        channel_purpose_desc = (
            "Please be mindful of channels and their uses. Bringing something up once is alright, however starting"
            " a long discussion about something that belongs in another channel, or posting the same thing across"
            " multiple channels, is not. If your post is off-topic from the subject of the channel, it may be deleted."
            " Repeat offenses will be punished. Check the description in each channel before posting as extended rules"
            " may exist for that channel."
        )
        divisive_topics_title = "Maintain civility when discussing controversial topics."
        divisive_topics_desc = (
            "For divisive topics (politics, religion, sexuality, etc.), please make sure that you conduct conversation"
            f" on those topics in {off_topic} appropriately and civilly. Due to the nature of such topics, they can"
            " easily escalate to toxic and heated arguments that will undoubtedly break other server rules if left"
            " unchecked. Please change the discussion topic if a moderator instructs you to, as otherwise you will"
            " be subject to punishment."
        )
        no_tos_violation_title = "No ToS violations or content related to piracy or illegal activities."
        no_tos_violation_desc = (
            "Promoting, linking to, or name-dropping ToS violating services will be considered a rule violation and"
            "  may be handled depending on the severity of the offense. We do not allow the distribution of links or"
            " information related to ToS violating and illegal software and will be removing all posts that contain"
            " links or how-tos on this information. Moderators will be on the lookout for links to pirated content"
            " and also software that provides an unfair game advantage. Discussing any illegal activity is strictly"
            " prohibited! Any criminal activity will be reported to the proper authorities."
        )
        clean_names_title = "Avoid names with obstructive characters."
        clean_names_desc = (
            "Anyone can change their nickname in this server using the `/nick` command. Remember, nicknames are"
            " server-only and will only change your name in this server. It won't affect any of your other servers."
            " Refrain from using too many special characters in your current display name. A couple of special symbols"
            " are fine so long as there is a normal alphanumeric name that people can easily type. For example,"
            ' "$ GolDenVeiL $" is fine, but "ƓօӀժҽղѵҽìӀ" is not. Should you break this rule, you will be asked'
            " to change your name or it will be changed for you. Repeat offenses of this rule will be punished."
        )
        no_nsfw_profile_title = "No inappropriate user avatars, names, or custom statuses."
        no_nsfw_profile_desc = (
            "You will be kicked from the server if your Discord profile picture, username, nickname, custom status, or"
            " any public profile attribute violates the server rules. Violating this rule repeatedly, or refusing to"
            " change the inappropriate aspect of your Discord profile to something more appropriate can get you"
            " banned."
        )
        no_ads_title = "No unapproved advertising of any kind."
        no_ads_desc = (
            "Do not advertise, link to, or sell your or any 3rd party services, products, bots, Discord servers or"
            " anything that may provide you financial benefit or compensation in any way. Creative content on a well"
            " known website (YouTube, DeviantArt, SoundCloud, etc.) is acceptable, as long as the content does not"
            " violate server rules. Otherwise, please message <@747112673786986577> to get moderator approval for what"
            " you intend to post first, or your link will be deleted and you may be punished depending on the severity"
            f" of the offense. Advertising streams must be limited to {stream_promo} *only*. Do not send"  # streams (and videos)
            " unsolicited DMs or ads to other members. If you receive any form of advertising from members in this"
            " server, please report it through <@747112673786986577>."
        )
        no_spamming_title = "No spamming or other disruptive behaviors."
        no_spamming_desc = (
            "Any actions considered to be spamming or otherwise disruptive or annoying will be punished. This includes"
            " but is not limited to flooding the chat with meaningless text, sending multiple messages where a single"
            " message would suffice, excessive emoji use, excessive caps spam, inciting spam, unnecessarily spreading"
            " your message into several lines of text, mic-spamming or making very loud and sustained noises, joining"
            " or leaving a voice chat repeatedly, spoiling a movie or TV show within 7 days of its release, being a"
            " general nuisance to others."
        )
        no_scamming_title = "Do not attempt to scam others."
        no_scamming_desc = (
            "There is no such thing as free Gold Coins! Trying to scam other members in any way is not allowed. This"
            " includes actively seeking personal information, linking scam websites, and encouraging other members to"
            " break the rules. If you encourage or bait other users into breaking a rule, you will be punished"
            " alongside them. Baiting users into clicking malicious links is strictly forbidden and is cause to ban."
            " We encourage you not to click on any links that appear suspicious."
        )
        no_impersonation_title = "No impersonation."
        no_impersonation_desc = (
            "Do not attempt to impersonate or roleplay as moderators or staff. The act of impersonating a moderator,"
            " administrator, Frostburn or Garena employees, or another famous person to intimidate or fool someone is"
            " strictly forbidden and will be subject to punishment up to and including an immediate ban. Do not pretend"
            " to be game support. You may help other members, but do not falsely imply that you have a role or other"
            " position of authority."
        )
        no_account_sale_title = "Do not attempt to sell, trade, or buy accounts."
        no_account_sale_desc = (
            "Account selling, buying, trading, and etc. is against the"
            " [Heroes of Newerth Account Terms of Service](https://www.heroesofnewerth.com/documents/tos/)"
            " everyone agrees to before playing the game. This is a bannable offense both in game and in this Discord"
            ' server and violates rule 3. Frostburn Studios Heroes of Newerth Account Terms of Service: *"Frostburn'
            " does not recognize the transfer of Frostburn or HoN accounts. You may not purchase, sell, gift or trade"
            " any Account, or offer to purchase, sell, gift or trade any Account, and any such attempt shall be null"
            ' and void."*'
        )
        no_alts_title = "No alternative accounts or punishment evasion."
        no_alts_desc = (
            "Users are discouraged from using alternative accounts (alts) on the HoN Discord, and those accounts will"
            " be kicked if found out. Using an alt specifically to evade a punishment is strictly forbidden and is"
            " cause for both the alt and main accounts to be banned from the server. Additionally, ban evasion is"
            " grounds for a minimum 1 year ban from the HoN Discord before you can appeal. If you want to appeal a"
            " mute or ban, create a modmail ticket by messaging <@747112673786986577>."
        )
        no_ban_discussion_title = "Do not argue publicly about punishments."
        no_ban_discussion_desc = (
            "The moderators of this Discord reserve the right to issue punishments as they see fit the rules above. Do"
            " not argue publicly in chat about punishments issued to yourself or other users. What staff say is final!"
            " If you feel that a specific moderator has made an error of judgement, has broken the rules themselves,"
            " or if you feel a rule is unfair or unjust, feel free to message <@747112673786986577> and we can reach"
            " a resolution calmly. Should you continue arguing about your punishments in public chat, your punishment"
            " will be escalated and you will lose the right to dispute it."
        )
        mod_help_title = "Moderator Help"
        mod_help_desc = (
            "All moderators on the official HoN Discord server are volunteers and do not work for Frostburn Studios."
            " The team cannot help with in-game problems, or provide technical or customer support. For all"
            " server-related issues, message <@747112673786986577>. The bot will create a thread for your inquiry and"  # enquiry
            f" alert active moderators to it. Do not ping {mod_mention}s unless there is an emergency that requires"
            " immediate intervention, such as a server raid or significant spam.\n\nIf you have any further questions"
            " about the rules and their enforcement, don't be afraid to ask a moderator or message"
            " <@747112673786986577>. The staff of this Discord server reserve the right to make alterations to the"
            " rules should the necessity arise."
        )

        embed_1 = discord.Embed(title="Rules & Guidelines", type="rich", description=description, color=0x3CC03C)
        # embed_1.set_author(name="Heroes of Newerth International")
        embed_1.add_field(name=f"1. {be_polite_title}", value=be_polite_desc, inline=False)
        embed_1.add_field(name=f"2. {no_nsfw_content_title}", value=no_nsfw_content_desc, inline=False)
        embed_1.add_field(name=f"3. {no_tos_violation_title}", value=no_tos_violation_desc, inline=False)
        embed_1.add_field(name=f"4. {no_spamming_title}", value=no_spamming_desc, inline=False)
        embed_1.add_field(name=f"5. {no_pings_title}", value=no_pings_desc, inline=False)
        embed_1.add_field(name=f"6. {channel_purpose_title}", value=channel_purpose_desc, inline=False)
        embed_1.add_field(name=f"7. {divisive_topics_title}", value=divisive_topics_desc, inline=False)
        embed_1.add_field(name=f"8. {clean_names_title}", value=clean_names_desc, inline=False)
        embed_1.add_field(name=f"9. {no_nsfw_profile_title}", value=no_nsfw_profile_desc, inline=False)
        embed_1.add_field(name=f"10. {no_account_sale_title}", value=no_account_sale_desc, inline=False)
        embed_1.set_footer(text="Page 1/2")

        embed_2 = discord.Embed(title="Rules & Guidelines", type="rich", description="", color=0x3CC03C)
        embed_2.add_field(name=f"11. {no_ads_title}", value=no_ads_desc, inline=False)
        embed_2.add_field(name=f"12. {no_impersonation_title}", value=no_impersonation_desc, inline=False)
        embed_2.add_field(name=f"13. {no_scamming_title}", value=no_scamming_desc, inline=False)
        embed_2.add_field(name=f"14. {no_alts_title}", value=no_alts_desc, inline=False)
        embed_2.add_field(name=f"15. {no_ban_discussion_title}", value=no_ban_discussion_desc, inline=False)
        embed_2.add_field(name=mod_help_title, value=mod_help_desc, inline=False)
        embed_2.set_footer(text="Page 2/2")

        return embed_1, embed_2

    async def intro(self) -> discord.Embed:
        emojis = self.ctx.guild.emojis
        facebook = discord.utils.get(emojis, name="Facebook")
        twitter = discord.utils.get(emojis, name="Twitter")
        reddit = discord.utils.get(emojis, name="Reddit")
        twitch = discord.utils.get(emojis, name="Twitch")
        youtube = discord.utils.get(emojis, name="YouTube")

        title = "Welcome to the official Heroes of Newerth International Discord server!"
        description = "Find teammates, meet friends, ask questions, and chat about all things HoN!"
        embed = discord.Embed(title=title, type="rich", description=description, color=0x3CC03C)
        # embed_1.set_author(name="Heroes of Newerth International")
        support = (
            "[Customer Support Helpdesk](http://support.heroesofnewerth.com/)"
            "\n[Community Technical Support](https://forums.heroesofnewerth.com/index.php?/forum/9-community-tech-support/)"
            "\n[Report-A-Player Portal](https://rap.heroesofnewerth.com/)"
            "\n[Heroes of Newerth Forums](https://forums.heroesofnewerth.com/)"
        )
        socials = (
            f"{str(facebook)} [facebook.com/heroesofnewerth](https://www.facebook.com/heroesofnewerth)"
            f"\n{str(twitter)} [@heroesofnewerth](https://twitter.com/heroesofnewerth)"
            f"\n{str(reddit)} [r/HeroesofNewerth](https://www.reddit.com/r/HeroesofNewerth/)"
            f"\n{str(twitch)} [twitch.tv/honcast](https://twitch.tv/honcast)"
            f"\n{str(youtube)} [Heroes of Newerth](https://www.youtube.com/channel/UC8bmZ0eQyz84YXbk44TCO6w)"
        )
        embed.add_field(
            name="Play Heroes of Newerth now!", value="https://www.heroesofnewerth.com/download/", inline=False
        )
        embed.add_field(name="Support & Useful Links", value=support, inline=False)
        embed.add_field(name="Socials", value=socials, inline=False)
        return embed

    async def channel_categories(self) -> discord.Embed:
        channels = self.ctx.guild.channels
        picking_phase = discord.utils.get(channels, name="picking-phase").mention
        general = discord.utils.get(channels, name="general").mention
        ask_for_help = discord.utils.get(channels, name="help").mention
        contributions = discord.utils.get(channels, name="contributions").mention
        community_content = discord.utils.get(channels, name="community-content").mention
        tournaments = discord.utils.get(channels, name="tournaments").mention
        alt_modes = discord.utils.get(channels, name="alternate-modes").mention
        off_topic = discord.utils.get(channels, name="off-topic").mention
        bot_playgrounds = discord.utils.get(channels, name="bot-playgrounds").mention
        memes = discord.utils.get(channels, name="memes").mention
        forests_of_caldavar = discord.utils.get(channels, name="forests-of-caldavar").mention
        mid_wars = discord.utils.get(channels, name="mid-wars").mention

        title = "Channel Categories"
        category_1_name = "Gates of Newerth"
        category_1_desc = (
            f"{picking_phase}: Claim roles by clicking on reactions! Some give you access to special channels such as"
            " regional LFG (Looking for Group)."
        )
        category_2_name = "General Text Channels"
        category_2_desc = (
            f"{general}: Talk about anything HoN related, but keep it English only!"
            f"\n{ask_for_help}: Ask for help from the community. Inquiries regarding suspensions **may not** be"
            " discussed here!"
            f"\n{contributions}: Do you have an artistic touch? Share your HoN related artwork, videos, or"
            " game modifications here!"
            f"\n{community_content}: Post screenshots or videos of your games and matches, discuss them, or simply"
            " enjoy them."
            f"\n{tournaments}: Talk about the current and upcoming tournaments."
            f"\n{alt_modes}: Talk about alternative modes such as Capture the Flag, Prophets, Devo Wars, Team"
            " Deathmatch, Soccer, etc. and find other people to play them with."
            f"\n{bot_playgrounds}: Check in-game statistics and interact with available bots through commands."
            f"\n{off_topic}: Anything that is not directly related or completely unrelated to HoN may be discussed"
            " here. Any and all rules still apply."
            f"\n{memes}: Share your dankest memes while keeping all rules in mind!"
        )
        category_3_name = "Balance & Design Discussions"
        category_3_desc = (
            f"{forests_of_caldavar}: Leave feedback about the current state of Forests of Caldavar in NAEU."
            " Discuss balance issues and talk about possible improvements."
            f"\n{mid_wars}: Discuss current issues with Mid Wars balance and design, suggest improvements."
        )
        category_4_name = "NA/EU/LAT/CIS/AUS"
        category_4_desc = (
            f"These will unlock depending on the roles you pick in {picking_phase} and will include a LFG text channel"
            " as well as a few voice channels for TMM groups."
        )
        category_5_name = "Voice Channels"
        category_5_desc = "To be used for playing HoN. Please do not idle in these channels."
        embed = discord.Embed(title=title, type="rich", description="", color=0x3CC03C)
        embed.add_field(name=category_1_name, value=category_1_desc, inline=False)
        embed.add_field(name=category_2_name, value=category_2_desc, inline=False)
        embed.add_field(name=category_3_name, value=category_3_desc, inline=False)
        embed.add_field(name=category_5_name, value=category_5_desc, inline=False)
        embed.add_field(name=category_4_name, value=category_4_desc, inline=False)
        return embed

    async def roles(self) -> discord.Embed:
        roles = self.ctx.guild.roles
        head_mod_mention = discord.utils.get(roles, name="Head Discord Moderator").mention
        mod_mention = discord.utils.get(roles, name="Discord Moderator").mention
        garena_mention = discord.utils.get(roles, name="Garena Staff").mention
        forstburn_mention = discord.utils.get(roles, name="Frostburn Staff").mention
        guardian_mention = discord.utils.get(roles, name="Guardian of Newerth").mention
        gm_mention = discord.utils.get(roles, name="Game Master").mention
        rct_mention = discord.utils.get(roles, name="Retail Candidate Tester").mention
        to_mention = discord.utils.get(roles, name="Tournament Organizer").mention
        reddit_mod_mention = discord.utils.get(roles, name="Reddit Moderator").mention
        streamer_mention = discord.utils.get(roles, name="Streamer").mention
        honored_mention = discord.utils.get(roles, name="HoNored").mention
        contributor_mention = discord.utils.get(roles, name="Contributor").mention
        nitro_mention = discord.utils.get(roles, name="Sol's Disciple").mention
        be_mention = discord.utils.get(roles, name="Balance Enthusiast").mention

        group_1 = (
            f"{head_mod_mention}: Moderator of moderators, in charge of the HoN Discord moderation team. Should issues"
            f" involving any of our {mod_mention} arise, this is who you want to talk to. Secretly feeds Bananas to"
            " Wumpus."
            f"\n\n{mod_mention}: Preservers of the order in chat. Moderators are neither Discord nor Frostburn"
            " Studios employees. They ensure the safety of the members and the server itself and keep the Discord of"
            " Wumpii pleased."
        )
        group_2 = (
            f"{garena_mention}: Given to Garena employees."
            f"\n\n{forstburn_mention}: Frostburn Studios employees. They are here on their own courtesy and will not "
            " handle customer support or RAP tickets via Discord. Please use the respective websites"
            " ([Support Helpdesk](https://support.heroesofnewerth.com/ 'support.heroesofnewerth.com'),"
            " [RAP Portal](https://rap.heroesofnewerth.com/ 'rap.heroesofnewerth.com')) for those purposes. Any advice"
            " given by Frostburn employees in <#735515144091598898> isn't official support and should be taken as-is."
        )
        group_3 = (
            f"{guardian_mention}: Verified volunteers who moderate the Volunteer Corner channel category on Discord."
            f"\n\n{gm_mention}: Verified Game Masters, Newerth's Lawmen. Together they saddle up and ride,"
            " bringing justice, law, and order to all corners of Newerth. You may ask them general RAP questions."
            " However, case specific inquiries may not be discussed; please refer to the"
            " [RAP Portal](https://rap.heroesofnewerth.com/ 'rap.heroesofnewerth.com')."
            f"\n\n{rct_mention}: Verified RCT members, Sol's Guard. Dedicated volunteers who take part in the testing of"
            " new patches and content up to a month before its official release. Their blessed shields shine orange"
            " beneath Sol's rays, imbued with his pure light and power. You may apply for this position"
            " [here](https://forums.heroesofnewerth.com/index.php?/application/ 'forums.heroesofnewerth.com')."
        )
        group_4 = (
            f"{to_mention}: Independent volunteers who organize tournaments which are officially sponsored by"
            " Frostburn Studios. Contrary to popular belief, they are rumored to share Kane's ideals."
            f"\n\n{reddit_mod_mention}: Moderators of the official Heroes of Newerth Reddit community,"
            " [r/HeroesofNewerth](https://www.reddit.com/r/HeroesofNewerth/ 'r/HeroesofNewerth')."
            f"\n\n{streamer_mention}: The select few who may promote their streams on Discord. This is a privilege."
            "  Please refrain from posting, sharing or promoting your stream in Discord channels without this role!"
        )
        group_5 = (
            f"{honored_mention}: Bestowed upon the greatest Sol's warriors, those who helped shape Newerth in all ways"
            " possible, by Sol himself. Without their commitment to the cause, Newerth would have never become"
            " what it is today. May Sol's light forever illuminate their path."
            f"\n\n{contributor_mention}: Fellow Newerthians who have proven their worth and left a notable mark in the"
            " community. Their vaillant efforts shall never be forgotten."
            f"\n\n{nitro_mention}: Gracious Newerthians who Nitro Boost the server."
            f"\n\n{be_mention}: Newerthians who stand out in the eyes of the almighty <@127605782840737793> regarding"
            " useful insight about balance and design. The last of Scout survivors."
        )

        # All Hells, The Scar, True Evil, The Bruning Ember, The First/Second/Third Corruption

        embed = discord.Embed(title="Roles", type="rich", description=group_1, color=0x3CC03C)
        # embed.set_author(name="Heroes of Newerth International")
        # embed.add_field(name="\u2063", value=group_1, inline=False)
        embed.add_field(name="\u2063", value=group_2, inline=False)
        embed.add_field(name="\u2063", value=group_3, inline=False)
        embed.add_field(name="\u2063", value=group_4, inline=False)
        embed.add_field(name="\u2063", value=group_5, inline=False)
        return embed

    async def reactions_regional_roles(self, region_emoji_names: dict) -> discord.Embed:
        desc = (
            "These give access to regional channel categories, including regional LFG (Looking for Group) channels.\n"
        )
        roles = self.ctx.guild.roles
        for emoji, role_name in region_emoji_names.items():
            role_mention = discord.utils.get(roles, name=role_name).mention
            desc += f"\n{emoji} - {role_mention}"
        footer = (
            "For regions other than Europe, flags were chosen based on the most spoken language and its associated"
            " country in that region."
        )

        embed = discord.Embed(title="Regional Roles", type="rich", description=desc, color=0x3CC03C)
        embed.set_footer(text=footer)
        return embed

    async def commands(self) -> discord.Embed:
        embed = discord.Embed(
            title="Heroes of Newerth International",
            type="rich",
            description=(
                "A list of <@681882801427316767> commands available only on Discord. Both `.` and `!` can be"
                " used as the command prefix. Commands on this list are written in the following format:"
                "\n```css\n.command subcommand [argument] {description}```"
            ),
            url="https://discord.gg/F7gQtUm",
            color=0x3CC03C,
            timestamp=self.ctx.message.created_at,
        )
        embed.set_author(name="Commands")
        embed.add_field(
            name="Statistics",
            value=(
                "```css"
                "\n.stats [nickname] {In-game player statistics for nickname. HoN NAEU/International only.}```"
            ),
            inline=False,
        )
        embed.add_field(
            name="Gambling", value="```css\n.roll [low] [high]```", inline=False,
        )
        embed.add_field(
            name="Miscellaneous",
            value="```css\n.signature {Purchase or configure Discord Embedded Signature.}```",
            inline=False,
        )
        # embed.add_field(name="Links (RCT Only)", value="```css\n.forums```", inline=False)
        embed.set_footer(text="RCTBot", icon_url="https://i.imgur.com/Ou1k4lD.png")
        embed.set_thumbnail(url="https://i.imgur.com/q8KmQtw.png")
        return embed


class HoNOfficial(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_client = AsyncDatabaseHandler.client
        self.db = self.db_client["hon"]
        self.config_collection = self.db["config"]
        # Default author and avatar.
        self.webhook_author = "Merrick"
        self.webhook_avatar_url = "https://i.imgur.com/874QFIb.png"  # HoN Web Logo: https://i.imgur.com/nsw8s2J.png
        # Reaction roles.
        self.guild_id_dict = {}  # {guild.id: {message.id: {emoji.name: role.name}}}
        self.synchronize.start()  # pylint: disable=no-member

    def cog_unload(self):
        self.synchronize.cancel()  # pylint: disable=no-member

    @tasks.loop(hours=12.0)
    async def synchronize(self):
        config = await self.config_collection.find_one({})
        # NOTE: All message ID keys are strings!
        self.guild_id_dict = {config["guild_id"]: config["reaction_roles"]}

    @commands.Cog.listener("on_raw_reaction_add")
    async def _reaction_roles(self, payload):
        # NOTE: All message ID keys are strings!
        if (
            payload.guild_id not in self.guild_id_dict
            or str(payload.message_id) not in self.guild_id_dict[payload.guild_id]
            or payload.emoji.name not in self.guild_id_dict[payload.guild_id][str(payload.message_id)]
        ):
            return
        guild = self.bot.get_guild(payload.guild_id)
        # member = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        role = discord.utils.get(
            guild.roles, name=(self.guild_id_dict[payload.guild_id][str(payload.message_id)][payload.emoji.name]),
        )
        if role not in payload.member.roles:
            await payload.member.add_roles(role, reason="Reaction")

        if role in payload.member.roles:
            await payload.member.remove_roles(role, reason="Reaction")
        await message.remove_reaction(payload.emoji, payload.member)

    async def _get_webhook(self, ctx, name: str) -> discord.Webhook:
        webhooks = await ctx.channel.webhooks()
        if not (webhook := discord.utils.get(webhooks, name=name)):
            async with aiohttp.ClientSession() as session:
                resp = await session.get(self.webhook_avatar_url)
                avatar_bytes = await resp.read()
                webhook = await ctx.channel.create_webhook(name=name, avatar=avatar_bytes)
        return webhook

    @commands.command()
    @checks.is_senior()
    async def botcmdlist(self, ctx):
        creator = EmbedCreator(ctx)
        commands_ = await creator.commands()
        await ctx.send(embed=commands_)
        await ctx.message.delete()

    @commands.group()
    @checks.is_senior()
    async def embed(self, ctx):
        pass

    @embed.command(name="rules")
    async def _embed_rules(self, ctx):
        creator = EmbedCreator(ctx)
        intro = await creator.intro()
        rules = await creator.rules()
        channels = await creator.channel_categories()
        roles = await creator.roles()
        embed_list = [intro, rules[0], rules[1], channels, roles]

        webhook = await self._get_webhook(ctx, "RCTBot Rules")
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(webhook.url, adapter=discord.AsyncWebhookAdapter(session))
            # Send individually due to a Discord limitation for large embedded messages.
            for embed in embed_list:
                await webhook.send(
                    username="The Blind Disciples", avatar_url="https://i.imgur.com/ql9KULC.png", embed=embed
                )
                # Delay to preserve order when sent to Discord.
                await asyncio.sleep(0.25)
        await ctx.message.delete()

    @embed.command(name="regions")
    async def _embed_regions(self, ctx):
        creator = EmbedCreator(ctx)
        dict_ = {
            "🇺🇸": "North America",
            "🇪🇺": "Europe",
            "🇧🇷": "Latin America",
            "🇷🇺": "Commonwealth of Independent States",
            "🇦🇺": "Australia",
        }
        embed = await creator.reactions_regional_roles(dict_)

        webhook = await self._get_webhook(ctx, "RCTBot Reaction Roles")
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(webhook.url, adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(username=self.webhook_author, embed=embed)

        # Webhook send does not return a message object, getting the most recent message from this channel in cache:
        await asyncio.sleep(1.25)
        message = ctx.channel.last_message
        for emoji in dict_:
            await message.add_reaction(emoji)

        # {message_id: {emoji_str: role_name}} NOTE: All keys are strings!
        message_reactions = {str(message.id): dict_}
        reaction_roles = (await self.config_collection.find_one({}))["reaction_roles"]
        reaction_roles = {**message_reactions, **reaction_roles}
        await self.config_collection.update_one({}, {"$set": {"reaction_roles": reaction_roles}})
        self.synchronize.restart()  # pylint: disable=no-member
        await ctx.message.delete()


# pylint: disable=unused-argument
def setup(bot):
    bot.add_cog(HoNOfficial(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
