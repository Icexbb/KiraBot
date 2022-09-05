from nonebot import Bot
from nonebot.adapters.onebot.v11 import Event

from kirabot.handler import Module

mo = Module('测试')
test1 = mo.add_service('test1', (1, 1, 1))


@test1.at_message("full", "私聊测试", (True, False, False), False, True)
async def test(bot: Bot, event: Event):
    await bot.send(event, '这是一条来自新生KiraBot框架的信息')


@test1.at_message("full", "群聊测试", (False, True, False), False, True)
async def test(bot: Bot, event: Event):
    await bot.send(event, '这是一条来自新生KiraBot框架的信息')


@test1.at_message("full", "频道测试", (False, False, True), False, True)
async def test(bot: Bot, event: Event):
    await bot.send(event, '这是一条来自新生KiraBot框架的信息')
