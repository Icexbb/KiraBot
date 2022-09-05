from typing import Callable, Tuple


class Function:
    def __init__(
            self,
            module_name: str,
            service_name: str,
            func: Callable,
            dm_only: bool = False,
            field: Tuple[int, int, int] | Tuple[bool, bool, bool] = (0, 1, 1),
            positive: bool = True
    ):
        """
        sv_name: str,服务名称
        func: Callable,功能函数
        dm_only: bool,是否为DM功能
        field: Tuple[int, int, int] = None,作用域
        positive: bool = True,是否为主动功能
        """
        self.module_name = module_name
        self.service_name = service_name
        self.func = func
        self.dm_only = dm_only
        self.field = field
        self.positive = positive
        self.name = func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
