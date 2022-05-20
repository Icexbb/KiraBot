from typing import List

from nonebot import on_message, Bot, on_notice, on_request
from nonebot.adapters import Event
from nonebot.exception import FinishedException

from .config import LOG_LANG
from .format import *
from .module import _loaded_modules, Module

message_processor = on_message()

event_property = [
    'anonymous', 'construct', 'copy', 'dict', 'font', 'from_orm', 'get_event_description',
    'get_event_name', 'get_log_string', 'get_message', 'get_plaintext', 'get_session_id', 'get_type',
    'get_user_id', 'group_id', 'is_tome', 'json', 'message', 'message_id', 'message_seq', 'message_type',
    'parse_file', 'parse_obj', 'parse_raw', 'post_type', 'raw_message', 'reply', 'schema', 'schema_json',
    'self_id', 'sender', 'sub_type', 'time', 'to_me', 'update_forward_refs', 'user_id', 'validate'
]
# group message event
'''time = 1652716148,
self_id = 3309659104,
post_type = 'message',
sub_type = 'normal',
user_id = 1072542936,
message_type = 'group',
message_id = -1883451115,
message = [MessageSegment(type='text', data={'text': '测试'})],
raw_message = '测试',

font = 0,
sender = Sender(
    user_id=1072542936,
    nickname='茶币币',
    sex='unknown', 
    age=0, 
    card='',
    area='', 
    level='',
    role='owner',
    title=''
),
to_me = False,
reply = None,
group_id = 879701242,
anonymous = None,
message_seq = 9726
'''
# channel message event
'''
time=1652716572,
self_id=3309659104,
post_type='message',
message_id='BABHYZGtKjd6AAAAAABORTcAAAAAAAAABw==',
self_tiny_id='144115218677776443',
user_id='144115218769595948',
message='测试',
guild_id='20092001649833850',
sender={
    'nickname': '茶币币',
    'tiny_id': '144115218769595948',
    'user_id': 144115218769595948
},
message_type='guild',
channel_id='5129527',
sub_type='channel'
'''
# private message event
'''
time=1652716733,
self_id=3309659104,
post_type='message',
sub_type='friend',
user_id=1072542936,
message_type='private',
message_id=-678291293,

message=[MessageSegment(type='text',data={'text': '测试'})],
raw_message='测试',
font=0,
sender = Sender(
    user_id = 1072542936,
    nickname='茶币币',
    sex='unknown',
    age=0,
    card=None,
    area=None,
    level=None,
    role=None,
    title=None
),
to_me=True,
reply=None,
target_id=3309659104
'''


@message_processor.handle()
async def handle_message(bot: Bot, event: Event, ):
    service_funcs: List[Module.Service.Function] = []
    for module_name in _loaded_modules:
        service_funcs += _loaded_modules[module_name].match(event)
    if service_funcs:
        positive_triggered = False
        for sf in service_funcs:

            if sf.dm_only and not event.is_tome():
                continue  # not to me, ignore.
            if not sf.sv.check_permission(event):
                continue  # permission denied.

            if sf.positive:
                if not positive_triggered:
                    sf.sv.logger.success(
                        SV_POSITIVELY_TRIGGERED[LOG_LANG].format(func_name=sf.name, mid=event.message_id))
                    try:
                        await sf.func(bot, event)
                    except FinishedException:
                        raise
                    except Exception as e:
                        sf.sv.logger.error(
                            SV_ERROR_HAPPENED[LOG_LANG].format(func_name=sf.name, mid=event.message_id,
                                                               ex_type=type(e)))
                        sf.sv.logger.exception(e)
                    positive_triggered = True
            else:
                try:
                    await sf.func(bot, event)
                except FinishedException:
                    raise
                except Exception as e:
                    sf.sv.logger.error(
                        SV_ERROR_HAPPENED[LOG_LANG].format(func_name=sf.name, mid=event.message_id,
                                                           ex_type=type(e)))
                    sf.sv.logger.exception(e)


notice_processor = on_notice()


@notice_processor.handle()
async def handle_notice(bot: Bot, event: Event):
    pass


request_processor = on_request()
REQUEST_TYPE = {
    'friend': {'main': ['user_id', 'comment', 'flag']},
    'group': {
        'main': ['sub_type', 'group_id', 'user_id', 'comment', 'flag'],
        'sub_type': ['add', 'invite']
    }
}


@request_processor.handle()
async def handle_request(bot: Bot, event: Event):
    pass
