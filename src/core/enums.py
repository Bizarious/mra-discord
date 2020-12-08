from enum import Enum


class Dates(Enum):
    DATE_FORMAT = "%d.%m.%y %H:%M:%S"
    DATE_FORMAT_DETAIL = "%d.%m.%y %H:%M:%S:%f"
    DATE_FORMAT_DATE_ONLY = "%d.%m.%y"
    TIME_FORMAT = "%H:%M:%S"
