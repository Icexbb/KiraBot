import re
from typing import List

from fuzzywuzzy import fuzz
from nonebot.adapters import Event
from nonebot.log import logger

from .function import Function
from .. import config
from ..config import NICKNAME
from ..format import *

MESSAGE_TRIGGER_TYPE = {
    'prefix': 0,
    'subfix': 1,
    'full': 2,
    'regex': 3,
    'keyword': 4,
    'fuzzy': 5
}
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


class MessageTrigger:
    class MainTrigger:
        def __init__(self):
            self.key: {str: Function} = {}

        def add_matcher(self, keys: str | list, function: Function):
            if type(keys) == str:
                keyword = [keys]
            else:
                keyword = keys
            for p in keyword:
                if p not in self.key:
                    self.key[p] = function
                else:
                    logger.error(
                        KEY_TRIGGER_ADD_ERROR.format(trigger=p))

        def match(self, message: str):
            raise NotImplementedError

    class Prefix(MainTrigger):
        def __init__(self) -> None:
            super().__init__()

        def match(self, message: str):
            matched_func: List[Function] = []
            for key in self.key:
                me = message
                func: Function = self.key[key]
                if func.dm_only:
                    for nickname in NICKNAME:
                        if re.search(nickname, me):
                            me = re.sub(nickname, '', me, 1)
                if me.startswith(key) and (func not in matched_func):
                    matched_func.append(func)
            return matched_func

    class Subfix(MainTrigger):
        def __init__(self) -> None:
            super().__init__()

        def match(self, message: str):
            matched_func: List[Function] = []
            for key in self.key:
                me = message
                func: Function = self.key[key]
                if func.dm_only:
                    for nickname in NICKNAME:
                        if re.search(nickname, me):
                            me = re.sub(nickname, '', me, 1)
                if me.endswith(key) and (func not in matched_func):
                    matched_func.append(func)
            return matched_func

    class FullMatch(MainTrigger):
        def __init__(self):
            super().__init__()

        def match(self, message: str):
            matched_func: List[Function] = []
            for key in self.key:
                me = message
                func: Function = self.key[key]
                if func.dm_only:
                    for nickname in NICKNAME:
                        if re.search(nickname, me):
                            me = re.sub(nickname, '', me, 1)
                if me == key and (func not in matched_func):
                    matched_func.append(func)
            return matched_func

    class Regex(MainTrigger):
        def __init__(self):
            super().__init__()

        def match(self, message: str):
            matched_func: List[Function] = []
            for key in self.key:
                me = message
                func: Function = self.key[key]
                if func.dm_only:
                    for nickname in NICKNAME:
                        if re.search(nickname, me):
                            me = re.sub(nickname, '', me, 1)
                if re.search(key, me) and (func not in matched_func):
                    matched_func.append(func)
            return matched_func

    class Keyword(MainTrigger):
        def __init__(self):
            super().__init__()

        def match(self, message: str):
            matched_func: List[Function] = []
            for key in self.key:
                me = message
                func: Function = self.key[key]
                if func.dm_only:
                    for nickname in NICKNAME:
                        if re.search(nickname, me):
                            me = re.sub(nickname, '', me, 1)
                if key in me and (func not in matched_func):
                    matched_func.append(func)
            return matched_func

    class Fuzzy(MainTrigger):
        def __init__(self):
            super().__init__()

        def match(self, message: str):
            matched_func: List[Function] = []
            for key in self.key:
                me = message
                func: Function = self.key[key]
                if func.dm_only:
                    for nickname in NICKNAME:
                        if re.search(nickname, me):
                            me = re.sub(nickname, '', me, 1)
                if fuzz.ratio(key, me) > config.fuzzy_rate:
                    matched_func.append(func)
            return matched_func

    def __init__(self):
        self.full = self.FullMatch()
        self.prefix = self.Prefix()
        self.subfix = self.Subfix()
        self.regex = self.Regex()
        self.keyword = self.Keyword()
        self.fuzzy = self.Fuzzy()
        self.trigger_chain: List[MessageTrigger.MainTrigger] = [
            self.prefix,
            self.subfix,
            self.full,
            self.regex,
            self.keyword,
            self.fuzzy
        ]

    def match(self, event: Event):
        function: List[Function] = []
        message = str(event.get_message())

        for trigger in self.trigger_chain:
            if s := trigger.match(message):
                function += s
        return function


class NoticeTrigger:
    def __init__(self):
        self.key: {str: {str: Function}} = {}
        self.type_list = ['notice_type', 'sub_type' or None]

    def add_matcher(self, keys: str | list, sf):
        sf: Function
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


message_trigger = MessageTrigger()
notice_trigger = NoticeTrigger()
