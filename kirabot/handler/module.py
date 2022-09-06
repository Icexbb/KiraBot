import re
from typing import Tuple

import nonebot

from .service import Service
from .. import auth
from ..format import *

_re_illegal_char = re.compile(r'[\\/:*?"<>|.]')


class Module:
    """
    Module 模块类
    """

    def __init__(
            self,
            name: str,
            field: Tuple[int, int, int] | Tuple[bool, bool, bool] = (0, 1, 1),
            _permission: int = auth.NORMAL,
    ):
        """
        定义插件模块类
        新建插件时应当定义唯一模块以实现全面管理
        """
        self.name = name
        self.field = field
        self.permission = _permission
        self.services: {str: Service} = {}
        assert not _re_illegal_char.search(name), r'Module name cannot contain character in `\/:*?"<>|.`'
        assert self.name not in loaded_modules, f'Module Name Duplicated'
        loaded_modules[self.name] = self

    def __getitem__(self, item) -> Service:
        if item in self.services:
            return self.services[item]
        else:
            raise KeyError("No Such Service")

    def add_service(
            self,
            name: str,
            field: Tuple[int, int, int] = None,
            visible: bool = True,
            enable: bool = True,
            _permission: int = None,
            guidance: str = None
    ) -> Service:
        new_service = Service(
            self.name, name,
            field=field or self.field,
            visible=visible,
            enable=enable,
            _permission=_permission or self.permission,
            guidance=guidance
        )
        assert not _re_illegal_char.search(name), r'Service name cannot contain character in `\/:*?"<>|.`'
        assert new_service.name not in self.services, f'Service Name Duplicated'
        self.services[new_service.name] = new_service
        nonebot.logger.opt(colors=True).success(SV_ADDED_INFO.format(module_name=self.name, service_name=name))
        return new_service

    @property
    def bot(self) -> nonebot.Bot:
        return nonebot.get_bot()


loaded_modules: {str: Module} = {}


def _change_area_service_availability(target_status: bool, area_id: str, service_to_change: Service):
    if target_status:
        if area_id in service_to_change.disabled_area:
            service_to_change.disabled_area.remove(area_id)
        if area_id not in service_to_change.enabled_area:
            service_to_change.enabled_area.append(area_id)
    else:
        if area_id not in service_to_change.disabled_area:
            service_to_change.disabled_area.append(area_id)
        if area_id in service_to_change.enabled_area:
            service_to_change.enabled_area.remove(area_id)
    service_to_change.save_config(service_to_change.update_config())


def set_module_status(area_id: str, target_status: bool, module_name: str, service_name: str = None):
    if module_name in loaded_modules:
        module_selected: Module = loaded_modules[module_name]
    else:
        raise ModuleNotFoundError
    if service_name:
        if service_name in module_selected.services:
            service_selected: Service = module_selected.services[service_name]
            _change_area_service_availability(target_status, area_id, service_selected)
            return
        else:
            raise ModuleNotFoundError
    else:
        for service_name_iter in module_selected.services:
            service_iter: Service = module_selected.services[service_name_iter]
            _change_area_service_availability(target_status, area_id, service_iter)


def get_module_help(module_name: str, service_name: str = None):
    guidance_dict: {str: str} = {}
    if module_name in loaded_modules:
        module_selected: Module = loaded_modules[module_name]
    else:
        raise ModuleNotFoundError
    if service_name:
        if service_name in module_selected.services:
            service_selected: Service = module_selected.services[service_name]
            guidance_dict[service_name] = service_selected.guidance
        else:
            raise ModuleNotFoundError
    else:
        for service_name_iter in module_selected.services:
            service_iter: Service = module_selected.services[service_name_iter]
            guidance_dict[service_name_iter] = service_iter.guidance
    return guidance_dict
