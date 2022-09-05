import datetime

from nonebot.adapters import Event

from .config import SUPERUSERS, get_config, update_config
from .utils import get_area_id

BLACK = BLOCK = 0
BLOCKED_FIELD = 5
NORMAL = 10
GUILD = 11
PRIVATE = 15
ADMIN = 20
OWNER = 30
WHITE = ALLOW = 50
SU = SUPERUSER = 100


class EventAuth:
    def __init__(self, event: Event):
        self.event = event
        self.event_dict = event.dict()
        self.user_id = str(self.event.get_user_id())
        self.self_id = self.event_dict['self_id']
        self.area_id = get_area_id(event)

    def get_user_permission(self):

        if str(self.user_id) in SUPERUSERS:
            return SU

        whitelist = get_config('white')
        if whitelist:
            if str(self.user_id) in whitelist:
                if whitelist[self.user_id]:
                    return WHITE

        blocklist = get_config('block')
        if blocklist:
            if self.user_id in blocklist:
                now = int(datetime.datetime.now().timestamp())
                if now > blocklist[self.user_id]:
                    del blocklist[self.user_id]
                    update_config(blocklist, 'block')
                else:
                    return BLOCK

        if self.event_dict['post_type'] == 'message':
            if self.area_id.startswith('u'):
                return PRIVATE
            elif self.area_id.startswith('g'):
                role = self.event_dict['sender']['role']
                if role == 'owner':
                    return OWNER
                elif role == 'admin':
                    return ADMIN
                else:
                    return NORMAL
            elif self.area_id.startswith('c'):
                return GUILD

        return NORMAL

    def set_block_user(self, td: datetime.timedelta, user_id: int = None):
        now = datetime.datetime.now()
        block_time = now + td
        blocklist = get_config('auth', 'block')
        blocklist[user_id or self.user_id] = (block_time.timestamp())
        update_config(blocklist, 'auth', 'block')

    def set_white_user(self, status: bool = True, user_id: int = None):
        whitelist = get_config('auth', 'white')
        whitelist[user_id or self.user_id] = status
        update_config(whitelist, 'auth', 'white')

    def get_filed_availability(self):
        auth_area = get_config('auth', 'area')
        if 'block' in auth_area:
            return BLOCK if self.area_id in auth_area['block'] else NORMAL

    def set_filed_availability(self, able: bool):
        auth_area = get_config('auth', 'area')
        if 'block' not in auth_area:
            auth_area['block'] = []
        if able:
            if self.area_id in auth_area['block']:
                auth_area['block'].remove(self.area_id)
                update_config(auth_area, 'auth', 'area')
                return WHITE
            else:
                return BLACK
        else:
            if self.area_id in auth_area['block']:
                return BLACK
            else:
                auth_area['block'].append(self.area_id)
                update_config(auth_area, 'auth', 'area')
                return WHITE
