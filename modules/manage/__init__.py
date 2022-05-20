from kirabot import auth
from kirabot.module import Module

mo = Module('Bot管理', (1, 1, 1), auth.SU)
mo.add_service('botManage')

@mo.botManage.at_message('','开启')