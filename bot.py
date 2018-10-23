import os
import discord
import asyncio
import logging

from discord.ext import commands
from simc import SimC

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

TOKEN = os.environ.get("DISCORD_TOKEN")

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    description='Quick sims in discord')

bot.add_cog(SimC(bot, "C:\Simulationcraft(x64)\simc"))


@bot.event
async def on_ready():
    print(f'Logged in as:\n{bot.user} (ID: {bot.user.id})')


bot.run(TOKEN)
