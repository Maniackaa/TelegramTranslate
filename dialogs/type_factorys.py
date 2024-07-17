import datetime
from config.bot_settings import settings, logger

def positive_int_check(text: str) -> str:
    if all(ch.isdigit() for ch in text) and 0 <= int(text):
        return text
    raise ValueError


def tel_check(text: str) -> str:
    digits = [x for x in text if x.isdigit()]
    if len(digits) < 5 or len(digits) > 12:
        raise ValueError
    return text


def time_check(text: str) -> str:
    try:
        datetime.datetime.strptime(text, '%H:%M')
    except Exception as err:
        logger.warning(err)
        raise ValueError
    return text


time = '23:50'
time = datetime.datetime.strptime(time, '%H:%M').time()
print(time)


y = datetime.datetime.combine(
    datetime.datetime(2023, 3, 1),
    time,
)
print(settings.tz.localize(y))
