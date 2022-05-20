import re
from functools import wraps
from typing import Callable
from typing import List
from typing import Tuple

import nonebot
from fuzzywuzzy import fuzz
from nonebot.adapters import Event
from nonebot_plugin_apscheduler import scheduler

from . import auth, config
from .auth import EventAuth
from .config import update_config, get_config, LOG_LANG
from .format import *

NOTICE_TYPE = {
    'group_upload': {'main': ['group_id', 'user_id', 'file'],
                     'file': ['id', 'name', 'size', 'busid']},
    'group_admin': {'main': ['sub_type', 'group_id', 'user_id'],
                    'sub_type': ['set', 'unset']},
    'group_decrease': {'main': ['sub_type', 'group_id', 'operator_id', 'user_id'],
                       'sub_type': ['leave', 'kick', 'kick_me']},
    'group_increase': {'main': ['sub_type', 'group_id', 'operator_id', 'user_id'],
                       'sub_type': ['approve', 'invite']},
    'group_ban': {'main': ['sub_type', 'group_id', 'operator_id', 'user_id', 'duration'], },
    'group_recall': {'main': ['group_id', 'user_id', 'operator_id', 'message_id']},
    'group_card': {'main': ['group_id', 'user_id', 'card_new', 'card_old']},

    'friend_add': {'main': ['user_id']},

    'friend_recall': {'main': ['user_id', 'message_id']},
    'notify': {
        'sub_type': {
            'poke': ['sender_id', 'group_id', 'user_id', 'target_id'],
            'lucky_king': ['user_id', 'target_id'],
            'honor': ['group_id', 'user_id', 'honor_type']
        }
    },
    'offline_file': {'main': ['user_id', 'file'], 'file': ['name', 'size', 'url']},
    'client_status': {'main': ['client_status', 'online']},
    'essence': {'main': ['sub_type', 'sender_id', 'operator_id', 'message_id'],
                'sub_type': ['add', 'delete']},
    'message_reaction': {'main': ['guild_id', 'channel_id', 'user_id', 'message_id', 'current_reactions']},
    'channel_updated': {"main": ['guild_id', 'channel_id', 'user_id', 'operator_id', 'old_info', 'new_info']},
    'channel_created': {'main': ['guild_id', 'channel_id', 'user_id', 'operator_id', 'channel_info']},
}

_re_illegal_char = re.compile(r'[\\/:*?"<>|.]')
_loaded_modules = {}


class Module:
    class Service:

        class Function:
            def __init__(
                    self,
                    sv,
                    func: Callable,
                    dm_only: bool,
                    field: Tuple[int, int, int] = None,
                    positive: bool = True
            ):
                self.sv: Module.Service = sv
                self.func = func
                self.dm_only = dm_only
                self.field = field or sv.field
                self.positive = positive
                self.name = func.__name__

            def __call__(self, *args, **kwargs):
                return self.func(*args, **kwargs)

        class MessageTrigger:

            class MainTrigger:
                def __init__(self):
                    self.key: {str: Module.Service.Function} = {}

                def add_matcher(self, keys: str | list, sf):
                    sf: Module.Service.Function
                    if type(keys) == str:
                        keyword = [keys]
                    else:
                        keyword = keys
                    for p in keyword:
                        if p not in self.key:
                            self.key[p] = sf
                        else:
                            sf.sv.logger.error(
                                KEY_TRIGGER_ADD_ERROR[LOG_LANG].format(trigger=p))

                def match(self, message: str):
                    raise NotImplementedError

            class Prefix(MainTrigger):
                def __init__(self) -> None:
                    super().__init__()

                def match(self, message: str):
                    matched_func: List[Module.Service.Function] = []
                    for key in self.key:
                        if message.startswith(key):
                            matched_func.append(self.key[key])
                    return matched_func

            class Subfix(MainTrigger):
                def __init__(self) -> None:
                    super().__init__()

                def match(self, message: str):
                    matched_func: List[Module.Service.Function] = []
                    for key in self.key:
                        if message.endswith(key):
                            matched_func.append(self.key[key])
                    return matched_func

            class FullMatch(MainTrigger):
                def __init__(self):
                    super().__init__()

                def match(self, message: str):
                    matched_func: List[Module.Service.Function] = []
                    for key in self.key:
                        if message == key:
                            matched_func.append(self.key[key])
                    return matched_func

            class Regex(MainTrigger):
                def __init__(self):
                    super().__init__()

                def match(self, message: str):
                    matched_func: List[Module.Service.Function] = []
                    for key in self.key:
                        if re.search(key, message):
                            matched_func.append(self.key[key])
                    return matched_func

            class Keyword(MainTrigger):
                def __init__(self):
                    super().__init__()

                def match(self, message: str):
                    matched_func: List[Module.Service.Function] = []
                    for key in self.key:
                        if key in message:
                            matched_func.append(self.key[key])
                    return matched_func

            class Fuzzy(MainTrigger):
                def __init__(self):
                    super().__init__()

                def match(self, message: str):
                    matched_func: List[Module.Service.Function] = []
                    for key in self.key:
                        if fuzz.ratio(key, message) > config.fuzzy_rate:
                            matched_func.append(self.key[key])
                    return matched_func

            def __init__(self):
                self.full = self.FullMatch()
                self.prefix = self.Prefix()
                self.subfix = self.Subfix()
                self.regex = self.Regex()
                self.keyword = self.Keyword()
                self.fuzzy = self.Fuzzy()
                self.trigger_chain = [
                    self.prefix,
                    self.subfix,
                    self.full,
                    self.regex,
                    self.keyword,
                    self.fuzzy
                ]
                self.trigger_list = {
                    'prefix': 0,
                    'subfix': 1,
                    'full': 2,
                    'regex': 3,
                    'keyword': 4,
                    'fuzzy': 5
                }

            def match(self, event: Event):
                function: List[Module.Service.Function] = []
                message = str(event.get_message())
                for trigger in self.trigger_chain:
                    if s := trigger.match(message):
                        function += s
                return function

        class NoticeTrigger:
            def __init__(self):
                self.key: {str: {str: Module.Service.Function}} = {}
                self.type_list = ['notice_type', 'sub_type' or None]

            def add_matcher(self, keys: str | list, sf):
                sf: Module.Service.Function
                if type(keys) == str:
                    keyword = [keys]
                else:
                    keyword = keys
                if keyword[0] in NOTICE_TYPE:
                    if keyword[0] not in self.key:
                        self.key[keyword[0]] = {}
                    k = 'main'
                    if keyword[0] in ['group_admin', 'group_decrease', 'group_increase', 'notify']:
                        if len(keyword) == 2:
                            k = keyword[1]
                    if k not in self.key[keyword[0]]:
                        self.key[keyword[0]] = []
                    self.key[keyword[0]].append(sf)
                else:
                    raise KeyError

            def match(self, notice_type: str | list[str]):
                sf_list = self.key
                if isinstance(notice_type, str):
                    notice_type = [notice_type]
                if len(notice_type) == 1:
                    try:
                        return sf_list[notice_type[0]]['main']
                    except KeyError:
                        return []
                else:
                    try:
                        return sf_list[notice_type[0]][notice_type[1]]
                    except KeyError:
                        return []

        def __init__(
                self,
                name: str,
                module,
                field: Tuple[int, int, int] = None,
                visible: bool = True,
                enable: bool = True,
                _permission: int = None,
                _help: str = None,

        ):
            self.name = name
            self.module: Module = module
            self.field = field or module.field
            self.permission = _permission or module.permission
            self.visible = visible
            self.enable = enable
            self.help = _help
            self.logger = nonebot.log.logger
            self.mtrigger = Module.Service.MessageTrigger()
            self.functions: {str: Module.Service.Function} = {}
            self.scheduler = scheduler

        @property
        def bot(self):
            return nonebot.get_bot()

        def at_message(
                self,
                trigger_type: str | int,
                trigger: str | list[str],
                field_type: Tuple[int, int, int] = None,
                direct: bool = False,
                positive: bool = None
        ) -> Callable:
            ttype = self.mtrigger.trigger_list[trigger_type] if isinstance(trigger_type, str) else trigger_type
            field_type = field_type or self.field or (0, 1, 1)
            positive = positive or False

            def deco(func) -> Callable:
                sf = self.Function(self, func, direct, field=field_type, positive=positive)
                self.mtrigger.trigger_chain[ttype].add_matcher(trigger, sf)
                return func

            self.logger.info(f"added Trigger {trigger_type} {trigger}")
            return deco

        def at_notice(
                self,
                trigger_type: str | list[str],
                positive: bool = None
        ) -> Callable:
            ttype = self.mtrigger.trigger_list[trigger_type] if isinstance(trigger_type, str) else trigger_type
            field_type = self.field or (0, 1, 1)
            positive = positive or False
            direct: bool = False

            def deco(func) -> Callable:
                sf = self.Function(self, func, direct, field=field_type, positive=positive)
                self.mtrigger.trigger_chain[ttype].add_matcher(trigger, sf)
                return func

            self.logger.info(f"added Trigger {trigger_type} {trigger}")
            return deco

        def at_scheduled(self, *args, **kwargs) -> Callable:
            kwargs.setdefault('misfire_grace_time', 60)
            kwargs.setdefault('coalesce', True)

            def deco(func: Callable) -> Callable:
                @wraps(func)
                async def wrapper():
                    try:
                        self.logger.info(
                            SV_SCHEDULED_JOB_RUN[LOG_LANG].format(
                                module=self.module.name,
                                service=self.name,
                                job=func.__name__
                            )
                        )
                        ret = await func()
                        self.logger.info(
                            SV_SCHEDULED_JOB_FINISHED[LOG_LANG].format(
                                module=self.module.name,
                                service=self.name,
                                job=func.__name__
                            )
                        )
                        return ret
                    except Exception as e:
                        self.logger.error(
                            SV_SCHEDULED_JOB_ERROR[LOG_LANG].format(
                                module=self.module.name,
                                service=self.name,
                                job=func.__name__,
                                exception=type(e)
                            )
                        )
                        self.logger.exception(e)

                return scheduler.scheduled_job(*args, **kwargs)(wrapper)

            nonebot.logger.info(f'added Scheduled Job {self.name}')
            return deco

        def check_permission(self, event: Event):
            user_permission = EventAuth(event).get_permission()
            return user_permission >= self.permission

        def save_config(self, data: dict):
            update_config(data, self.name)

        def load_config(self):
            data = get_config(self.name)
            if not data:
                data = {
                    "name": self.name,
                    "user_permission": self.permission,
                    "enable": self.enable,
                    "visible": self.visible,
                    "help": self.help,
                    "enabled_group": [],
                    "disabled_group": [],
                    "enabled_channel": [],
                    "disabled_channel": [],
                    "enable_field": [0, 1, 1]
                }
                self.save_config(data)
            return data

        def match(self, event: Event):
            return self.mtrigger.match(event)

    def __init__(
            self,
            name: str,
            field: Tuple[int, int, int] = (0, 1, 1),
            _permission: int = auth.NORMAL,
    ):
        self.name = name
        self.field = field
        self.permission = _permission
        self.services: {str: Module.Service} = {}
        assert not _re_illegal_char.search(name), r'Module name cannot contain character in `\/:*?"<>|.`'
        assert self.name not in _loaded_modules, f'Module Name Duplicated'
        _loaded_modules[self.name] = self

    def add_service(self, name, **kwargs):
        new_service = Module.Service(name, self, **kwargs)
        assert not _re_illegal_char.search(name), r'Service name cannot contain character in `\/:*?"<>|.`'
        assert new_service.name not in self.services, f'Service Name Duplicated'
        self.services[new_service.name] = new_service
        nonebot.logger.info(SV_ADDED_INFO[LOG_LANG].format(module_name=self.name, service_name=name))

    def __getattr__(self, item) -> Callable | Service:
        try:
            return self.__getattribute__(item)
        except AttributeError:
            if item in self.services:
                return self.services[item]
            else:
                raise AttributeError(f'Module {self.name} object has no attribute or loaded service {item.__name__}')

    def match(self, event: Event):
        field_list = ['private', 'group', 'guild']
        functions: List[Module.Service.Function] = []
        for service in self.services:
            functions += self.services[service].match(event)
        functions = [function for function in functions if
                     function.field[field_list.index(event.dict()['message_type'])]]
        return functions

    @property
    def bot(self):
        return nonebot.get_bot()
