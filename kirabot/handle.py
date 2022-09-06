from typing import Tuple

from nonebot import on_message, Bot, on_notice, on_request
from nonebot.adapters import Event
from nonebot.exception import FinishedException
from nonebot.log import logger

from .format import *
from .handler.function import Function
from .handler.module import loaded_modules, Module
from .handler.service import Service
from .handler.trigger import message_trigger
from .utils import get_area_id

message_processor = on_message()

event_property = [
    'anonymous', 'construct', 'copy', 'dict', 'font', 'from_orm', 'get_event_description',
    'get_event_name', 'get_log_string', 'get_message', 'get_plaintext', 'get_session_id', 'get_type',
    'get_user_id', 'group_id', 'is_tome', 'json', 'message', 'message_id', 'message_seq', 'message_type',
    'parse_file', 'parse_obj', 'parse_raw', 'post_type', 'raw_message', 'reply', 'schema', 'schema_json',
    'self_id', 'sender', 'sub_type', 'time', 'to_me', 'update_forward_refs', 'user_id', 'validate'
]


@message_processor.handle()
async def handle_message(bot: Bot, event: Event):
    positive_triggered = False
    area_id = get_area_id(event)
    functions = message_trigger.match(event)
    for function in functions:
        if positive_triggered and function.positive:
            continue

        module: Module = loaded_modules[function.module_name]
        if not check_field(area_id, module):
            continue

        service: Service = module.services[function.service_name]
        if not check_field(area_id, service):
            continue
        if not service.check_permission(event):
            continue  # permission denied.
        if not service.check_availability(event):
            continue

        if not check_field(area_id, function):
            continue
        if function.dm_only and not event.is_tome():
            continue  # not to me, ignore.

        if function.positive:
            service.logger.opt(colors=True).success(
                SV_POSITIVELY_TRIGGERED.format(
                    func_name=function.name,
                    mid=event.dict()["message_id"],
                )
            )
            await trigger_function(function, bot, event)
            positive_triggered = True
        else:
            await trigger_function(function, bot, event)


def check_field(area_id: str, item: Function | Service | Module):
    field: Tuple[int, int, int] | Tuple[bool, bool, bool] = item.field
    if area_id.startswith('u') and not field[0]:
        return False
    elif area_id.startswith('g') and not field[1]:
        return False
    elif area_id.startswith('c') and not field[2]:
        return False
    return True


async def trigger_function(function: Function, bot: Bot, event: Event):
    try:
        await function.func(bot, event)
    except FinishedException:
        raise
    except Exception as e:
        logger.error(
            SV_ERROR_HAPPENED.format(
                module=function.module_name,
                sv=function.service_name,
                func=function.name,
                message_id=event.dict()["message_id"],
                exception=type(e)
            ))
        logger.exception(e)


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
