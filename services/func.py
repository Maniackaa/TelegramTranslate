import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

from config.bot_settings import settings, logger


def get_data_from_info_string(info: str) -> dict:
    # info:137:ru
    splitted = info.split(':')
    index = splitted[1]
    lang_code = splitted[2]
    return {
        'index': index,
        'lang_code': lang_code
    }


def get_info_string_from_message(text: str):
    split = text.split('\n')
    info_string = split[-1]
    if info_string.startswith('info:'):
        return info_string


async def send_tg_message(ids_to_send: list[str], text: str, entities=None):
    if entities is None:
        entities = list()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties())
    for tg_id in ids_to_send:
        try:
            await bot.send_message(tg_id, text, entities=entities)
            await asyncio.sleep(0.1)
            logger.info(f'Сообщение {tg_id} отправлено')
        except TelegramForbiddenError as err:
            logger.warning(f'Ошибка отправки сообщения для {tg_id}: {err}')
        except Exception as err:
            logger.error(f'ошибка отправки сообщения пользователю {tg_id}: {err}', exc_info=False)