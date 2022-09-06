import importlib
import json

import nonebot

from .__bot__ import *

# load handler configs

for module in MODULES_ON:
    try:
        importlib.import_module('kirabot.config.' + module)
        nonebot.logger.info(f'成功加载 "{module}"的配置文件')
    except ModuleNotFoundError:
        # logger.warning(f'Not found config of "{handler}"')
        pass
json_config_data = os.path.dirname(__file__) + f'/data/'
if not os.path.exists(json_config_data):
    os.mkdir(json_config_data)


def get_config(key: str, subkey: str = None):
    path = json_config_data + f'{key}.json'
    if os.path.exists(path):
        data = json.load(open(path, 'r', encoding='utf-8'))
        if subkey:
            if subkey in data:
                return data[subkey]
            else:
                return {}
        else:
            return data
    else:
        return {}


def update_config(udata, key: str, subkey: str = None):
    path = json_config_data + f'{key}.json'
    if os.path.exists(path):
        data = json.load(open(path, 'r', encoding='utf-8'))
        if subkey:
            data[subkey] = udata
        else:
            data = udata
        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, ensure_ascii=False, indent=4)
    else:
        data = {subkey: udata}
        with open(path, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, ensure_ascii=False, indent=4)
