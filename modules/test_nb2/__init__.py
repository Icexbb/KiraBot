from nonebot import Bot
from nonebot.adapters.onebot.v11 import Event

from kirabot.module import Module

mo = Module('测试')
mo.add_service('test1')


@mo.test1.at_message("full", "私聊测试", [1, 0, 0], False, True)
async def test(bot: Bot, event: Event):
    await bot.send(event, '这是一条来自新生KiraBot框架的信息')


@mo.test1.at_message("full", "群聊测试", [0, 1, 0], False, True)
async def test(bot: Bot, event: Event):
    await bot.send(event, '这是一条来自新生KiraBot框架的信息')


@mo.test1.at_message("full", "频道测试", [0, 0, 1], False, True)
async def test(bot: Bot, event: Event):
    await bot.send(event, '这是一条来自新生KiraBot框架的信息')
