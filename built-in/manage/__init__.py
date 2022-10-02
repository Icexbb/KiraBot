import re

from nonebot import Bot
from nonebot.adapters import Event

from kirabot import auth
from kirabot.handler import Module, set_module_status, loaded_modules, Service
from kirabot.handler.module import get_module_help
from kirabot.utils import get_area_id

mo = Module('Bot管理器', (1, 1, 1), auth.ADMIN, )
module_manager = mo.add_service('模块管理', _permission=auth.ADMIN)
bot_manager = mo.add_service('Bot管理', _permission=auth.BLOCK)


@module_manager.at_message(
    'regex', r'(?P<mode>开启|启用|关闭|禁用)(?P<module>[^\\/:*?"<>|.\s\n]+)(\.(?P<service>[^\\/:*?"<>|.\s\n]+))?',
    (1, 1, 1),
    direct=True, positive=True)
async def module_manage(bot: Bot, event: Event):
    match = event.match[f"{module_manager.re_pointer}.module_manage"]
    mode = True if match.group("mode") in ['开启', '启用'] else False
    module_name = match.group("module")
    service_name = match.group("service")
    mod = [module_name]
    if service_name:
        mod.append(service_name)
    area_id = get_area_id(event)
    try:
        fin = set_module_status(area_id, mode, module_name, service_name)
    except ModuleNotFoundError:
        await bot.send(event, f'服务管理失败: {"模块" if not service_name else "服务"} {".".join(mod)}不存在')
    except Exception as e:
        await bot.send(event, f'服务管理失败: {e}')
        module_manager.logger.exception(e)
    else:
        if fin:
            await bot.send(event,
                           f'已{"开启" if mode else "关闭"}{"模块" if not service_name else "服务"} {".".join(mod)}',
                           at_sender=True)
        else:
            await bot.send(event, f'服务 {".".join(mod)} 在该区域内不可用 无法操作', at_sender=True)


@module_manager.at_message("full", ["模块列表", "功能列表"], (1, 1, 1), True, True)
async def module_show(bot: Bot, event: Event):
    enabled_mark = '[●]'
    disabled_mark = '[Ｘ]'
    message = {}
    for module_name in loaded_modules:
        module: Module = loaded_modules[module_name]
        service_list: list[Service] = [
            module.services[service_name]
            for service_name in module.services
            if module.services[service_name].visible
        ]
        res_list = []
        for sv in service_list:
            if not service_list.index(sv) == (len(service_list) - 1):
                tabs = "┣"
            else:
                tabs = "┗"
            if sv.check_availability(event):
                mark = enabled_mark
            else:
                mark = disabled_mark
            res_list.append(f"{mark} {tabs} {sv.name}")

        message[module_name] = ("\n".join(res_list)).strip()

    msg = "Bot模块列表:\n" + "\n".join([f"{mn}\n{message[mn]}" for mn in message]).strip()
    await bot.send(event, msg.strip())


@module_manager.at_message("prefix", ["帮助", "指南"], (1, 1, 1), True, True)
async def module_help(bot: Bot, event: Event):
    msg = str(event.get_message())
    mod = re.sub(r'^(帮助)|(指南)', '', msg).strip().split('.')
    module_name = mod[0]
    service_name = mod[1] if len(mod) > 1 else None
    try:
        helps = get_module_help(module_name, service_name)
    except ModuleNotFoundError:
        await bot.send(event, f'获取帮助文档失败: {"模块" if not service_name else "服务"} {".".join(mod)}不存在')
    else:
        msg = f'{"模块" if not service_name else "服务"} {".".join(mod)} 帮助文档:\n' + \
              "\n".join([f"{hp}:\n{helps[hp] if helps[hp] else '编写者未为该服务编写帮助文档'}" for hp in helps])
        await bot.send(event, msg)


@bot_manager.at_message('full', ['关机', '休眠', '开机', '启动'], (False, True, True), positive=True, direct=True)
async def bot_manage(bot: Bot, event: Event):
    event_auth = auth.EventAuth(event)
    field_auth = event_auth.get_area_availability()
    # operator_auth = event_auth.get_user_permission()
    # ev_message = event.get_message()
    # print(event.dict())

    if field_auth < auth.ADMIN:
        msg = "bot仅能由管理员及以上权限开启和关闭"
        await bot.send(event=event, message=msg, at_sender=True)
        return
