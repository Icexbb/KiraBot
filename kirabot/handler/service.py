import asyncio
from functools import wraps
from typing import Callable
from typing import Tuple

import nonebot
from nonebot import Bot
from nonebot.adapters import Event
from nonebot_plugin_apscheduler import scheduler

from .function import Function
from .trigger import MESSAGE_TRIGGER_TYPE, message_trigger, notice_trigger
from .. import auth
from ..config import update_config, get_config
from ..format import *
from ..utils import get_area_id


class Service:

    def __init__(
            self,
            module_name: str,
            name: str,
            field: Tuple[int, int, int] | Tuple[bool, bool, bool] = None,
            visible: bool = True,
            enable: bool = True,
            _permission: int = None,
            guidance: str = None,
    ):
        self.module_name = module_name
        self.name = name
        self_dict = self.load_config()

        self.field = field or (0, 1, 1)
        self.permission = _permission or auth.NORMAL
        self.visible = visible
        self.enable = enable
        self.guidance = guidance
        self.logger = nonebot.log.logger
        self.functions: {str: Function} = {}
        self.scheduler = scheduler
        self.enabled_area = self_dict["enabled_area"] or []
        self.disabled_area = self_dict["disabled_area"] or []

    @property
    def bot(self) -> Bot:
        """
        bot接口
        """
        return nonebot.get_bot()

    def at_message(
            self,
            trigger_type: str | int,
            trigger: str | list[str],
            field_type: Tuple[int, int, int] | Tuple[bool, bool, bool] = None,
            direct: bool = False,
            positive: bool = None
    ) -> Callable:
        """
        消息触发任务
        触发类型见kirabot.handler.trigger
        trigger_type :触发类型
         - 'prefix': 0, 前缀匹配
         - 'subfix': 1, 后缀匹配
         - 'full': 2, 全文匹配
         - 'regex': 3, 正则表达式匹配
         - 'keyword': 4, 关键词匹配
         - 'fuzzy': 5 模糊匹配
        field_type:触发区规定 Tuple[bool](私聊,群聊,频道) 为真时可触发
        direct:是否需要@才能触发
        positive:是否是主动行为 为假可同步触发其他非主动行为
        """
        ttype = MESSAGE_TRIGGER_TYPE[trigger_type] if isinstance(trigger_type, str) else trigger_type
        field_type = field_type or self.field or (0, 1, 1)
        positive = positive or False

        def deco(func) -> Callable:
            sf = Function(self.module_name, self.name, func, direct, field_type, positive)
            message_trigger.trigger_chain[ttype].add_matcher(trigger, sf)
            return func

        self.logger.debug(f"added Message Trigger {trigger_type} {trigger}")
        return deco

    def at_notice(self, trigger_type: str | list[str], positive: bool = None) -> Callable:
        """
        事件触发任务
        trigger_type:触发类型见kirabot.handler.trigger
        positive:是否是主动行为 为假可同步触发其他非主动行为

        """
        field_type = self.field or (0, 1, 1)
        positive = positive or False
        direct: bool = False

        def deco(func) -> Callable:
            sf = Function(self.module_name, self.name, func, direct, field_type, positive)
            notice_trigger.add_matcher(trigger_type, sf)
            return func

        self.logger.debug(f"added Notice Trigger {trigger_type}")
        return deco

    def at_scheduled(self, *args, **kwargs) -> Callable:
        """
        定时器触发任务
        """
        kwargs.setdefault('misfire_grace_time', 60)
        kwargs.setdefault('coalesce', True)

        def deco(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper():
                try:
                    self.logger.info(
                        SV_SCHEDULED_JOB_RUN.format(
                            module=self.module_name,
                            service=self.name,
                            job=func.__name__
                        )
                    )
                    ret = await func()
                    self.logger.info(
                        SV_SCHEDULED_JOB_FINISHED.format(
                            module=self.module_name,
                            service=self.name,
                            job=func.__name__
                        )
                    )
                    return ret
                except Exception as e:
                    self.logger.error(
                        SV_SCHEDULED_JOB_ERROR.format(
                            module=self.module_name,
                            service=self.name,
                            job=func.__name__,
                            exception=type(e)
                        )
                    )
                    self.logger.exception(e)

            return scheduler.scheduled_job(*args, **kwargs)(wrapper)

        nonebot.logger.debug(f'added Scheduled Job {self.name}')
        return deco

    def check_permission(self, event: Event):
        """
        检查事件的权限值是否满足执行该服务的任务
        """
        user_permission = auth.EventAuth(event).get_user_permission()
        return user_permission >= self.permission

    def check_availability(self, event: Event):
        area_id = get_area_id(event)
        if self.enable:
            if area_id in self.disabled_area:
                return False
        else:
            if area_id not in self.enabled_area:
                return False
        return True

    async def broadcast(self, msg: str, at_all: bool = False, interval: float = 0.5):
        """
        服务广播
        msg:str 要进行广播的信息
        at_all:bool 是否要@全体成员
        interval:float 每条信息发送时的间隔
        """
        config = self.load_config()
        groups = [gid for gid in config['enabled_area'] if gid.startswith('g')]
        guilds = [gid for gid in config['enabled_area'] if gid.startswith('c')]
        users = [gid for gid in config['enabled_area'] if gid.startswith('u')]
        if at_all:
            msg += "[CQ:at,qq=all]"
        for area_id in users:
            try:
                await asyncio.sleep(interval)
                # await self.bot.send_private_msg(group_id=gid, msg=msg)
            except Exception as e:
                self.logger.error(f'Exception {e} in Send Message To User {area_id}')

        for area_id in groups:
            try:
                group_id = area_id[1:]
                await asyncio.sleep(interval)
                await self.bot.send_group_msg(group_id=group_id, message=msg)
            except Exception as e:
                self.logger.error(f'Exception {e} in Send Message To Group {area_id}')
        for area_id in guilds:
            try:
                guild_id, channel_id = area_id[1:].split('-')
                await asyncio.sleep(interval)
                await self.bot.send_guild_channel_msg(guild_id=guild_id, channel_id=channel_id, message=msg)
            except Exception as e:
                self.logger.error(f'Exception {e} in Send Message To Guild {area_id}')

    def save_config(self, data: dict):
        """
        保存服务配置
        """
        update_config(data, self.module_name, self.name)

    def load_config(self):
        """
        加载服务配置
        """
        data = get_config(self.module_name)
        if data:
            if self.name not in data:
                try:
                    en_area = self.enabled_area
                except AttributeError:
                    en_area = []
                try:
                    dis_area = self.disabled_area
                except AttributeError:
                    dis_area = []
                data[self.name] = {
                    "name": self.name,
                    "enabled_area": en_area,
                    "disabled_area": dis_area,
                }
                update_config(data, self.module_name)
            return data[self.name]
        else:
            return {
                "name": self.name,
                "enabled_area": [],
                "disabled_area": [],
            }

    def update_config(self) -> dict:
        """
        返回当前配置（dict）:
        {
            "name":服务名,
            "enabled_area":启用区域,
            "disabled_area":关闭区域
        }
        """
        data = {
            "name": self.name,
            "enabled_area": self.enabled_area,
            "disabled_area": self.disabled_area,
        }
        return data
