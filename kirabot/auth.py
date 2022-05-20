import datetime

from nonebot.adapters import Event

from .config import SUPERUSERS, get_config, update_config

BLACK = BLOCK = 0
NORMAL = 10
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

    def get_permission(self):
        if self.user_id in SUPERUSERS:
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
            if self.event_dict['message_type'] == 'private':
                return PRIVATE
            elif self.event_dict['message_type']:
                role = self.event_dict['sender']['role']
                if role == 'owner':
                    return OWNER
                elif role == 'admin':
                    return ADMIN
                return NORMAL

    def set_block_user(self, td: datetime.timedelta):
        now = datetime.datetime.now()
        block_time = now + td
        blocklist = get_config('block')
        blocklist[self.user_id] = (block_time.timestamp())
        update_config(blocklist, 'block')

    def set_white_user(self, status: bool = True):
        whitelist = get_config('white')
        whitelist[self.user_id] = status
        update_config(whitelist, 'white')
