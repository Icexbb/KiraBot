from datetime import datetime

from nonebot import Bot
from nonebot.adapters import Event

from kirabot import auth
from kirabot.handler import Module
from kirabot.utils import async_get_json

Help_Command = '''
看看今天的番/今天有什么番/今日番剧 查看今天更新的番剧
看看明天的番/明天有什么番/明日番剧 查看明天更新的番剧
'''.strip()
Help_Announcer = '''
使用"Bot管理"模块开启本服务 将在每天固定时间推送今天/明天会更新的番剧
'''.strip()
Module_Bangumi = Module("Bangumi", (1, 1, 1))
Service_Command = Module_Bangumi.add_service(
    "番剧板",
    enable=True,
    guidance=Help_Command
)
Service_Announcer = Module_Bangumi.add_service(
    "推送板",
    (0, 1, 1),
    enable=False,
    _permission=auth.ADMIN,
    guidance=Help_Announcer
)


async def get_bangumi(date: int = None) -> list:
    if not date:
        now = datetime.now().weekday() + 1
    else:
        now = date
    header = {
        "User-Agent": "icexbb/Hoshino-KiraBot"
    }
    data: list = await async_get_json("https://api.bgm.tv/calendar", headers=header)
    for day in data:
        if day['weekday']['id'] == now:
            return day['items']


def render_bangumi(items: list) -> list:
    result = []
    for item in items:

        name = item['name_cn'] if item['name_cn'] else item['name']
        if ("rating" not in item) or ("rank" not in item) or (item['type'] != 2):
            continue
        score = item['rating']['score']
        rating_num = item['rating']['total']
        rank = item['rank']
        result.append(
            {
                'name': name,
                'score': score,
                'rating_num': rating_num,
                'rank': rank
            }
        )

    def take_rating_num(elem):
        return elem['rank']

    res1 = [x for x in result if x['rank'] and x['score']]
    res1.sort(key=take_rating_num)

    return [f'{item["name"]} 排名：{item["rank"]} 评分：{item["score"]}' for item in res1]


@Service_Announcer.at_scheduled('cron', hour="9", minute="0")
async def morning_anime():
    data = await get_bangumi()
    texts = render_bangumi(data)
    msg = f"今天将会更新的番剧在这里！\n（不包含无评分番剧）\n" + '\n'.join(texts) + "\n追番人记得跟剧〜"
    await Service_Announcer.broadcast(msg)


@Service_Announcer.at_scheduled('cron', hour="23", minute="30")
async def morning_anime():
    now = datetime.now().weekday() + 2
    if now == 8:
        now = 1
    data = await get_bangumi(now)
    texts = render_bangumi(data)
    msg = f"明天将会更新的番剧在这里！\n（不包含无评分番剧）\n" + '\n'.join(texts) + "\n追番人记得跟剧〜"
    await Service_Announcer.broadcast(msg)


@Service_Command.at_message("full", ["看看今天的番", "今天有什么番", "今日番剧"], positive=True)
async def morning_anime(bot: Bot, ev: Event):
    data = await get_bangumi()
    texts = render_bangumi(data)
    msg = f"今天将会更新的番剧在这里！\n（不包含无评分番剧）\n" + '\n'.join(texts) + "\n追番人记得跟剧〜"
    await bot.send(ev, msg)


@Service_Command.at_message("full", ["看看明天的番", "明天有什么番", "明日番剧"], positive=True)
async def morning_anime(bot: Bot, ev: Event):
    now = datetime.now().weekday() + 2
    if now == 8:
        now = 1
    data = await get_bangumi(now)
    texts = render_bangumi(data)
    msg = f"明天将会更新的番剧在这里！\n（不包含无评分番剧）\n" + '\n'.join(texts) + "\n追番人记得跟剧〜"
    await bot.send(ev, msg)
