import base64
import json
import os
import time
from collections import defaultdict
from datetime import datetime
from io import BytesIO

import nonebot
from PIL import Image

from .format import MODULE_NOT_EXIST_ERROR


def load_config(inbuilt_file_var):
    """
    Just use `config = load_config(__file__)`,
    you can get the config.json as a dict.
    """
    filename = os.path.join(os.path.dirname(inbuilt_file_var), 'config.json')
    try:
        with open(filename, encoding='utf8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        nonebot.logger.exception(e)
        return {}


def base64image(pic: Image) -> str:
    buf = BytesIO()
    pic.save(buf, format='PNG')
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return 'base64://' + base64_str


class FreqLimiter:
    def __init__(self, name: str, default_cd_seconds: int | float):
        self.name = name
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def get_data(self):
        return load_json(None, ['FreqLimiter'], f'{self.name}.json')

    def update_data(self, data: dict = None):
        if not data:
            data = self.next_time
        save_json(data, None, ['FreqLimiter'], f'{self.name}.json')

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

    def get_data(self):
        data = load_json(None, ['DailyNumberLimiter'], f'{self.name}.json')
        date = datetime.today().strftime('%y%m%d')
        if date in data:
            return data[date]
        else:
            self.update_data({date: {}})
            return {}

    def update_data(self, data: dict = None):
        date = datetime.today().strftime('%y%m%d')
        next_data = {date: data}
        save_json(next_data, None, ['DailyNumberLimiter'], f'{self.name}.json')

    def check(self, key) -> bool:
        data = self.get_data()
        if key not in data:
            count = data[key]
        else:
            count = 0
        return bool(count < self.max)

    def get_num(self, key):
        data = self.get_data()
        if key in data:
            return data[key]
        else:
            return 0

    def increase(self, key, num=1):
        data = self.get_data()
        data[key] = self.get_num(key) + 1
        self.update_data(data)

    def reset(self, key):
        data = self.get_data()
        data[key] = 0
        del data[key]
        self.update_data(data)


def render_list(lines, prompt="") -> str:
    n = len(lines)
    if n == 0:
        return prompt
    if n == 1:
        return prompt + "\n┗" + lines[0]
    return prompt + "\n┣" + "\n┣".join(lines[:-1]) + "\n┗" + lines[-1]


def load_json(module: str = None, path: list[str] = None, file: str = None):
    fpath = os.path.dirname(__file__)
    if module:
        fpath += f"/module/{module}/"
        if not os.path.exists(fpath):
            nonebot.logger.error(MODULE_NOT_EXIST_ERROR.format(module=module))
            raise FileExistsError
        fpath += 'data/' + '/'.join(path)
        os.makedirs(fpath, exist_ok=True)
        if not file.endswith('.json'):
            file += '.json'
        fpath += file
    else:
        fpath += '/data/'
        if not os.path.exists(fpath):
            os.makedirs(fpath, exist_ok=True)
        fpath += 'data/' + '/'.join(path)
        os.makedirs(fpath, exist_ok=True)
        if not file.endswith('.json'):
            file += '.json'
        fpath += file
    if not os.path.exists(fpath):
        return None
    else:
        try:
            data = json.load(
                open(fpath, 'r', encoding='utf-8')
            )
            if data:
                return data
            else:
                return None
        except json.JSONDecodeError:
            os.remove(fpath)
            return None


def save_json(data: dict | list, module: str = None, path: list[str] = None, file: str = None):
    fpath = os.path.dirname(__file__)
    if module:
        fpath += f"/module/{module}/"
        if not os.path.exists(fpath):
            nonebot.logger.error(MODULE_NOT_EXIST_ERROR.format(module=module))
            raise FileExistsError
    else:
        fpath += '/data/'
        if not os.path.exists(fpath):
            os.makedirs(fpath, exist_ok=True)

    fpath += 'data/' + '/'.join(path)
    os.makedirs(fpath, exist_ok=True)
    if not file.endswith('.json'):
        file += '.json'
    fpath += file

    with open(fpath, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
