import asyncio
import os

import nonebot
import nonebot.log
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
from nonebot.log import logger, default_format

from . import config, format
from .format import NOT_INIT_ERROR, NOT_RUNNING_ERROR

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
        self.path = os.path.dirname(__file__)

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
        for built_in_module in config.BUILT_IN_MODULE:
            try:
                nonebot.load_plugin(f'built-in.{built_in_module}')
            except Exception as e:
                nonebot.logger.exception(e)

        for module_name in config.MODULES_ON:
            try:
                self.load_plugin(module_name)
            except Exception as e:
                nonebot.logger.exception(e)
        from .handle import handle_message
        self.initialized = True

    def run(self, **kwargs):
        if not self.initialized:
            try:
                self.init(**kwargs)
            except Exception:
                raise RuntimeError(format.NOT_INIT_ERROR)

        try:
            self.running = True
            nonebot.run()
        except KeyboardInterrupt:
            nonebot.logger.info("Accept KeyBoardInterrupt")
        finally:
            nonebot.logger.info("NoneBot Exited")
            exit()

    def load_plugin(self, module_name: str):
        module_path = os.path.join(self.path, f"../modules/{module_name}")
        module_files = [
            file.removesuffix(".py") for file in os.listdir(module_path)
            if os.path.isfile(os.path.join(module_path, file))
            if os.path.splitext(os.path.join(module_path, file))[-1] == ".py"
        ]
        if "__init__" in module_files:
            nonebot.load_plugin(f"modules.{module_name}")
            module_files.remove("__init__")
        for file in module_files:
            nonebot.load_plugin(f"modules.{module_name}.{file}")

    def get_bot(self):
        if not self.initialized:
            raise ValueError(NOT_INIT_ERROR)
        elif not self.running:
            raise ValueError(NOT_RUNNING_ERROR)
        else:
            self.bot = nonebot.get_bot()
            return self.bot


bot = KiraBot()
