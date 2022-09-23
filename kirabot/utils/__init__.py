import base64
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

from PIL import Image
from nonebot import logger
from nonebot.adapters.onebot.v11 import Event, Bot
from nonebot.exception import ActionFailed

from ..config import RESOURCE, SELF_ID, RNAME, SUPERUSERS


def chain_reply(msgs: list, bot_name: str = RNAME, bot_uid: int | str = SELF_ID[0]) -> list:
    """
    列表内消息转换为可合并转发格式
    """
    chain = [{
        "type": "node",
        "data": {
            "name": str(bot_name),
            "uin": str(bot_uid),
            "content": str(msg),
        }
    } for msg in msgs]
    return chain


def _pic2b64(pic: Image.Image) -> str:
    buf = BytesIO()
    pic.save(buf, format='PNG')
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return 'base64://' + base64_str


def pic2cq(pic: Image.Image | str):
    """图片转换为base64格式CQ码"""
    if type(pic) == Image:
        pass
    elif type(pic) in [str]:
        pic: Image.Image = Image.open(pic)
    return f'[CQ:image,file={_pic2b64(pic)}]'


class FreqLimiter:
    def __init__(self, name: str, default_cd_seconds: int | float):
        self.name = name
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def get_data(self):
        return load_json(f'{self.name}.json', ['FreqLimiter'], )

    def update_data(self, data: dict = None):
        if not data:
            data = self.next_time
        save_json(data, f'{self.name}.json', ['FreqLimiter'])

    def check(self, key) -> bool:
        data = self.get_data()
        status = bool(time.time() >= data[key])
        if status:
            del data[key]
        return status

    def start_cd(self, key, cd_time=0):
        self.next_time[key] = time.time() + (cd_time if cd_time > 0 else self.default_cd)
        self.update_data(self.next_time)

    def left_time(self, key) -> float:
        left_t = self.next_time[key] - time.time()
        if left_t <= 0:
            left_t = 0
            del self.next_time[key]
        self.update_data(self.next_time)
        return left_t


class DailyNumberLimiter:

    def __init__(self, name: str, max_num: int):
        self.name = name
        self.today = -1
        self.count = defaultdict(int)
        self.max = max_num

    def _get_data(self):
        data = load_json(f'{self.name}.json', ['DailyNumberLimiter']) or {}
        date = datetime.today().strftime('%y%m%d')
        if date in data:
            return data[date]
        else:
            self.update_data({date: {}})
            return {}

    def update_data(self, data: dict = None):
        date = datetime.today().strftime('%y%m%d')
        next_data = {date: data}
        save_json(next_data, f'{self.name}.json', ['DailyNumberLimiter'])

    def check(self, key) -> bool:
        if not isinstance(key, str):
            key = str(key)
        count = self._get_num(key)
        return bool(count < self.max)

    def _get_num(self, key):
        data = self._get_data()
        if key in data:
            return data[key]
        else:
            return 0

    def increase(self, key, num=1):
        data = self._get_data()
        data[key] = self._get_num(key) + num
        self.update_data(data)

    def reset(self, key):
        data = self._get_data()
        data[key] = 0
        del data[key]
        self.update_data(data)


def render_list(lines: list, prompt: str = "") -> str:
    """生成制表符格式文本
    prompt:文本前缀
    """
    n = len(lines)
    if n == 0:
        return prompt
    if n == 1:
        return prompt + "\n┗" + lines[0]
    return prompt + "\n┣" + "\n┣".join(lines[:-1]) + "\n┗" + lines[-1]


def _get_json_file_path(file_name: str = None, res_path: list[str] = None):
    file_root = RESOURCE + '/data/'
    file_root = os.path.join(file_root, "/".join(res_path))
    os.makedirs(file_root, exist_ok=True)
    if not file_name.endswith('.json'):
        file_name += '.json'
    # file_root += file_name
    file_path = os.path.join(file_root, file_name)
    return file_path


def load_json(file_name: str = None, res_path: list[str] = None):
    file_path = _get_json_file_path(file_name, res_path)
    if not os.path.exists(file_path):
        return None
    else:
        try:
            data = json.load(open(file_path, 'r', encoding='utf-8'))
            if data:
                return data
            else:
                return None
        except json.JSONDecodeError:
            os.remove(file_path)
            return None


def save_json(data: dict | list, file_name: str = None, res_path: list[str] = None):
    file_path = _get_json_file_path(file_name, res_path)

    with open(file_path, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def get_area_id(event: Event) -> str:
    ev_dict = event.dict()
    if ev_dict['message_type'] == 'group':
        area_id = f"g{ev_dict['group_id']}"
    elif ev_dict['message_type'] == 'guild':
        area_id = f'c{ev_dict["guild_id"]}-{ev_dict["channel_id"]}'
    else:
        area_id = f'u{ev_dict["user_id"]}'
    return area_id


async def silence(bot: Bot, ev: Event, ban_time, skip_su=True):
    area_id = get_area_id(event=ev)
    if area_id.startswith('g'):
        try:
            uid = ev.get_user_id()
            if skip_su and uid in SUPERUSERS:
                return
            await bot.set_group_ban(self_id=ev.self_id, group_id=area_id[1:], user_id=uid,
                                    duration=ban_time)
        except ActionFailed as e:
            if 'NOT_MANAGEABLE' in str(e):
                return
            else:
                logger.error(f'禁言失败 {e}')
        except Exception as e:
            logger.exception(e)


def num2week(week_id: int) -> str:
    week_str = "星期一星期二星期三星期四星期五星期六星期日"
    pos = (week_id - 1) * 3
    return week_str[pos:pos + 3]


def timedelta2str(timed: timedelta) -> str:
    sec = int(timed.total_seconds())
    d, h = divmod(sec, 3600 * 24)
    h, r = divmod(h, 3600)
    m, s = divmod(r, 60)
    result = f'{str(d) + "天" if d else ""}{str(h) + "时" if h else ""}' \
             f'{str(m) + "分" if m else ""}{str(s) + "秒" if s else ""}'.strip()
    return result
