import asyncio
import os

import nonebot
import nonebot.log
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.log import logger, default_format

from . import config, format

os.makedirs('./log/', exist_ok=True)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class KiraBot:
    def __init__(self):
        self.running = False
        self.config = None
        self.initialized = False
        self.bot = None
        self.app = None
        self.driver = None

    def init(self, **kwargs):
        logger.add("./log/error.log", level="ERROR",
                   format=default_format, rotation="10MB")
        nonebot.init(**kwargs)

        self.app = nonebot.get_asgi()
        self.driver = nonebot.get_driver()
        self.driver.register_adapter(ONEBOT_V11Adapter)
        self.config = nonebot.config.Config

        nonebot.load_plugin('nonebot_plugin_guild_patch')
        nonebot.load_plugin('nonebot_plugin_apscheduler')
        for module_name in config.MODULES_ON:
            try:
                nonebot.load_plugin(f'modules.{module_name}')
            except Exception as e:
                nonebot.logger.exception(e)
        from .handle import handle_message
        self.initialized = True

    def run(self, **kwargs):
        if not self.initialized:
            try:
                self.init(**kwargs)
            except Exception:
                raise RuntimeError(format.NOT_INIT_ERROR[config.LOG_LANG])
        nonebot.logger.success('Scheduler Started')

        try:
            self.running = True
            nonebot.run()
        except KeyboardInterrupt:
            nonebot.logger.info("Accept KeyBoardInterrupt")
        finally:
            nonebot.logger.info("NoneBot Exited")
            exit()

    def get_bot(self):
        if not self.initialized:
            raise ValueError('KiraBot 未初始化')
        elif not self.running:
            raise ValueError('KiraBot 未在运行')
        else:
            self.bot = nonebot.get_bot()
            return self.bot


bot = KiraBot()
