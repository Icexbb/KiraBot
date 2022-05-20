import asyncio

from kirabot import bot

loop = asyncio.new_event_loop()

bot.run(loop=loop)
