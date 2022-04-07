from typing import Union

from core.bot import Bot
from core.task.task_base import TASK_FIELD_OWNER, TASK_FIELD_CHANNEL

_converter_table = {
    TASK_FIELD_OWNER: lambda value, bot: bot.get_user(value),
    TASK_FIELD_CHANNEL: lambda value, bot: bot.get_channel(value),
}


def convert_task_field(field_name: str, field_value: Union[str, int], bot: Bot):
    return _converter_table.get(field_name, lambda v, _: v)(field_value, bot)
