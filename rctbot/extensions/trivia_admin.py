# (c) 2020 ziep

import os
import asyncio

import discord
from discord.ext import commands

import rctbot.config
from rctbot.core.driver import AsyncDatabaseHandler

from rctbot.extensions.trivia_config import TriviaConfig

# from rctbot.extensions.trivia import TriviaGame


os.environ["PYTHONASYNCIODEBUG"] = "1"


class TriviaAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_client = AsyncDatabaseHandler.client
        self.db = self.db_client["Trivia"]
        self.q_qol = self.db["QUESTIONS"]

    @commands.group(aliases=["tra"], invoke_without_command=True)
    @commands.has_any_role(*(TriviaConfig.document["admin_roles"]))
    async def triviaadmin(self, ctx):
        await ctx.send_help("tra")

    @triviaadmin.command()
    async def set(self, ctx, key: str, value):
        await TriviaConfig.set(key, value)

    @triviaadmin.command()
    async def get(self, ctx, key: str):
        await ctx.send(await TriviaConfig.get(key))

    @triviaadmin.command(aliases=["lsqs", "lsq", "questionlist"])
    async def listquestions(self, ctx):
        questions = []
        for q in await self.q_qol.find({}).to_list(length=None):
            questions.append(q["_id"])
        await ctx.send(questions)

    @triviaadmin.command(aliases=["aq"])
    @commands.max_concurrency(1)
    async def addquestion(self, ctx, *, q=None):
        """Add question"""
        self.q_qol = self.db["QUESTIONS"]
        question = {
            "_id": max([x["_id"] for x in (await (self.q_qol.find({})).to_list(length=None))]) + 1,
            "enabled": True,
        }
        go = True

        def check(msg):
            return msg.author.id == ctx.author.id

        if not q:
            await ctx.send("Enter a question, for example: 'What is the square root of 4?'")
            if go:
                try:
                    question["question"] = (await self.bot.wait_for("message", timeout=120.0, check=check)).content
                    if question["question"] == "exit":
                        go = False
                except asyncio.TimeoutError:
                    await ctx.send("No question entered")
        else:
            question["question"] = q
        if (found := (await (self.q_qol.find({"question": question["question"]})).to_list(length=None))) :
            await ctx.send(f"❗ That question already exists!\n{found}")
            go = False
        if go:
            await ctx.send("Enter the answer(s) seperated by a comma. For example: 2,+2,-2,+-2,-+2")
            try:
                question["answers"] = (
                    (await self.bot.wait_for("message", timeout=120.0, check=check))
                    .content.replace(", ", ",")
                    .replace(" ,", ",")
                    .split(",")
                )
                if question["answers"][0] == "exit":
                    go = False
            except asyncio.TimeoutError:
                await ctx.send("No answers entered")
        if go:
            await ctx.send("Enter the category or '-' to skip")
            try:
                category = (await self.bot.wait_for("message", timeout=120.0, check=check)).content
                if category == "-":
                    question["category"] = None
                elif category == "exit":
                    go = False
                else:
                    question["category"] = category
            except asyncio.TimeoutError:
                await ctx.send("No category entered")
                question["category"] = None
        if go:
            await ctx.send("Enter a hint or '-' to skip")
            try:
                hint = (await self.bot.wait_for("message", timeout=120.0, check=check)).content
                if hint == "-":
                    question["hint"] = None
                elif hint == "exit":
                    go = False
                else:
                    question["hint"] = hint
            except asyncio.TimeoutError:
                await ctx.send("No hint entered")
                question["hint"] = None
            while go:
                await ctx.send(
                    f"**Add question to the database?**\n"
                    f"Respond with `yes` to confirm or `no` to cancel\n"
                    f'**ID**          : {question["_id"]}\n'
                    f'**Enabled**     : {question["enabled"]}\n'
                    f'**Question**    : {question["question"]}\n'
                    f'**Answers**     : {question["answers"]}\n'
                    f'**Category**    : {question["category"]}\n'
                    f'**Hint**        : {question["hint"]}\n'
                )

                try:
                    confirm = await self.bot.wait_for("message", timeout=120.0, check=check)
                    if confirm.content.lower() == "yes":
                        await self.q_qol.insert_one(question)
                        await confirm.add_reaction("👌")
                        break
                    elif confirm.content.lower() == "no":
                        await ctx.send("Aborting..")
                        break
                except asyncio.TimeoutError:
                    await ctx.send("Aborting..")
                    break
        if not go:
            await ctx.send("Aborting..")

    @triviaadmin.command(aliases=["gq"])
    async def getquestion(self, ctx, attr, *, args):
        """<attr> <*args>"""
        attr = attr.lower()
        question = await (await self.fetch_question(attr, args=args)).to_list(length=None)
        embed = discord.Embed(title="Question Info")
        if question:
            for q in question:
                embed.add_field(
                    name="\u2063",
                    value=(
                        f'**ID**          : {q["_id"]}\n'
                        f'**Enabled**     : {q["enabled"]}\n'
                        f'**Question**    : {q["question"]}\n'
                        f'**Answers**     : {q["answers"]}\n'
                        f'**Category**    : {q["category"]}\n'
                        f'**Hint**        : {q["hint"]}\n'
                    ),
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Couldn't find a question with attribute {attr}: {args}")

    async def fetch_question(self, attr, *, args, one: bool = False):
        attr = "answers" if attr == "answer" else attr
        attr = attr.replace("id", "_id")
        print(attr, args, one)
        if attr == "_id":
            args = int(args)
        if not one:
            return self.q_qol.find({attr: args})
        else:
            return await (self.q_qol.find_one({attr: args}))

    @triviaadmin.command(aliases=["mq", "modify"])
    async def modifyquestion(self, ctx, id: int, attr, *, args):
        """<id> <attr> <*args>"""
        question_doc = await (self.fetch_question(attr="id", args=id, one=True))
        print(question_doc)
        if question_doc:
            prepare_doc = dict(question_doc)
            prepare_doc[attr] = args
            print(question_doc)
            embed = discord.Embed(title="Confirm", description="Respond with 'yes' to confirm or 'no' to cancel.")
            embed.add_field(
                name="OLD",
                value=(
                    f'**ID**          : {question_doc["_id"]}\n'
                    f'**Enabled**     : {question_doc["enabled"]}\n'
                    f'**Question**    : {question_doc["question"]}\n'
                    f'**Answers**     : {question_doc["answers"]}\n'
                    f'**Category**    : {question_doc["category"]}\n'
                    f'**Hint**        : {question_doc["hint"]}\n'
                ),
            )
            embed.add_field(
                name="NEW",
                value=(
                    f'**ID**          : {prepare_doc["_id"]}\n'
                    f'**Enabled**     : {prepare_doc["enabled"]}\n'
                    f'**Question**    : {prepare_doc["question"]}\n'
                    f'**Answers**     : {prepare_doc["answers"]}\n'
                    f'**Category**    : {prepare_doc["category"]}\n'
                    f'**Hint**        : {prepare_doc["hint"]}\n'
                ),
            )
            await ctx.send(embed=embed)

            def check(msg):
                return msg.author.id == ctx.author.id

            while True:
                try:
                    confirm = await self.bot.wait_for("message", timeout=120.0, check=check)
                    if confirm.content.lower() == "yes":
                        await self.q_qol.find_one_and_replace(question_doc, prepare_doc)
                        await confirm.add_reaction("👌")
                        break
                    elif confirm.content.lower() == "no":
                        await ctx.send("Aborting..")
                        break
                except asyncio.TimeoutError:
                    await ctx.send("Aborting..")
                    break

        else:
            await ctx.send(f"Couldn't find a question with ID: {id}")

    @triviaadmin.command()
    async def disable(self, ctx, question_id: int):
        """<id> Disable a question"""
        question_doc = self.q_qol.find_one_and_update({"_id": question_id}, {"$set": {"enabled": False}})
        if question_doc:
            await ctx.message.add_reaction("👌")
        else:
            await ctx.send(f"Couldn't find a question with ID: {question_id}")

    @triviaadmin.command()
    async def enable(self, ctx, question_id: int):
        """<id> Enable a question"""
        question_doc = self.q_qol.find_one_and_update({"_id": question_id}, {"$set": {"enabled": True}})
        if question_doc:
            await ctx.message.add_reaction("👌")
        else:
            await ctx.send(f"Couldn't find a question with ID: {question_id}")


def setup(bot):
    bot.add_cog(TriviaAdmin(bot))
    rctbot.config.LOADED_EXTENSIONS.append(__loader__.name)


def teardown(bot):
    bot.remove_cog(TriviaAdmin(bot))
    rctbot.config.LOADED_EXTENSIONS.remove(__loader__.name)
