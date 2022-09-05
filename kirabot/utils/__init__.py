import base64
import json
import os
import time
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from typing import Union

import aiohttp
import requests
from PIL import Image
from aiosocksy.connector import ProxyConnector, ProxyClientRequest
from nonebot import logger
from nonebot.adapters.onebot.v11 import Event

from ..config import RESOURCE, SELF_ID, RNAME, PROXIES, PROXY


def chain_reply(msgs: list, bot_name: str = RNAME, bot_uid: int = SELF_ID[0]) -> list:
    """
    列表内消息转换为可合并转发格式
    """
    chain = [{
        "type": "node",
        "data": {
            "name": str(bot_name),
            "uin": str(bot_uid),
            "content": str(msg),
        },
    } for msg in msgs]
    return chain


async def async_get_json(url: str, proxy: bool = False, headers: dict = None, params: dict = None) -> Union[dict, list]:
    """异步获取json内容"""
    try:
        async with aiohttp.ClientSession(
                connector=ProxyConnector(), request_class=ProxyClientRequest, headers=headers,
        ) as session:
            async with session.get(url, params=params, proxy=PROXY if proxy else None) as response:
                try:
                    res = await response.json()
                except Exception as e:
                    logger.warning(f'Exception {e} Happened')

                    res = json.loads(await response.text('utf-8'), strict=False)
    except Exception as e:
        logger.warning(f'Async get {url} json data Failed, Try normally. Exception {e}')
        response = requests.get(url, params, headers=headers,
                                proxies=PROXIES if proxy else None)
        try:
            res = response.json()
        except Exception as e:
            logger.warning(f'Exception {e} Happened')
            res = json.loads(response.text, strict=False)
    return res


async def async_download(url: str, path: str, filename: str, proxy: bool = False, headers: dict = None):
    """异步下载文件"""
    async with aiohttp.ClientSession(
            connector=ProxyConnector(), request_class=ProxyClientRequest, headers=headers
    ) as session:
        async with session.get(url, proxy=PROXY if proxy else None) as response:
            if not response.status == 200:
                return False
            content = await response.read()
            with open(path + filename, 'wb') as file_output:
                file_output.write(content)
                return True


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
        data = load_json(f'{self.name}.json', ['DailyNumberLimiter'])
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
        data = self._get_data()
        if key not in data:
            count = data[key]
        else:
            count = 0
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
    file_root += file_name
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
