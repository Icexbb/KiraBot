# matcher
PRE_TRIGGER_ADD_ERROR = [
    "Prefix Trigger {trigger} is already Exist.", "前缀触发器{trigger}已经被添加"]
SUB_TRIGGER_ADD_ERROR = [
    "Subfix Trigger {trigger} is already Exist.", "后缀触发器{trigger}已经被添加"]
FULL_TRIGGER_ADD_ERROR = [
    "Full Match Trigger {trigger} is already Exist.", "全匹配触发器{trigger}已经被添加"]
REX_TRIGGER_ADD_ERROR = [
    "Regex Trigger {trigger} is already Exist.", "正则触发器{trigger}已经被添加"]
KEY_TRIGGER_ADD_ERROR = [
    "Keyword Trigger {trigger} is already Exist.", "关键词触发器{trigger}已经被添加"]
# handler
MODULE_NOT_EXIST_ERROR = [
    "Module {handler} not Exists", "模块{handler}不存在"
]
NOT_INIT_ERROR = [
    "KiraBot is Not Initialed", "KiraBot尚未初始化"
]
SV_NAME_EXISTED_ERROR = [
    "Service Name {name} Existed.", "服务名{name}已存在"
]

SV_POSITIVELY_TRIGGERED = [
    'Message {mid} Positively Triggered Function <green>{func_name}</green>',
    '消息 {mid} 积极触发了服务: <green>{func_name}</green>'
]
SV_ERROR_HAPPENED = [
    'A {ex_type} Exception Happened When Function {func_name} Processing Message {mid}',
    '服务 {func_name} 在处理消息 {mid} 时发生了异常 {ex_type}'
]
SV_ADDED_INFO = [
    'Service {service_name} Added to Module {module_name}',
    '在模块{module_name}中添加了服务{service_name}'
]
SV_SCHEDULED_JOB_RUN = [
    'Scheduled Job {handler}.{handler}.{job} Start',
    '计划任务 {handler}.{handler}.{job} 开始',
]
SV_SCHEDULED_JOB_FINISHED = [
    'Scheduled Job {handler}.{handler}.{job} Finished',
    '计划任务 {handler}.{handler}.{job} 完成',
]
SV_SCHEDULED_JOB_ERROR = [
    'Scheduled Job {handler}.{handler}.{job} Caused a {exception} Exception ',
    '计划任务 {handler}.{handler}.{job} 引起了错误 {exception}',
]
