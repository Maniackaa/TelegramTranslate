import asyncio
import pickle
import time
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.raw.functions.messages import TranslateText
from pyrogram.types import Message, TranslatedText, InlineKeyboardMarkup, InlineKeyboardButton

from parse_entities import parse_entities, message_to_html, replace_key
from config.bot_settings import logger, settings

BASE_DIR = Path(__file__).resolve().parent


client = Client(name='userbbot',
             api_id=settings.API_ID,
             api_hash=settings.API_HASH, parse_mode=ParseMode.HTML)


def get_data_from_info_string(info: str):
    # info:137:ru
    splitted = info.split(':')
    index = splitted[1]
    lang_code = splitted[2]
    return {'index': index, 'lang_code': lang_code}


# Прием оргинального сообщения. От бота в группу
@client.on_message(filters.chat(chats=[settings.GROUP_TRANSLATE]) & filters.incoming & filters.user(users=[settings.BOT_ID]))
async def to_group(client: Client, message: Message):
    logger.debug('Принято сообщение от бота')
    #info:137:ru
    split = message.text.split('\n')
    info_text = split[-1]
    data = get_data_from_info_string(info_text)
    lang_codes = settings.CHANNEL_CODES
    for lang_code in lang_codes:
        translated = await client.translate_text(to_language_code=lang_code,
                                                 text=message.text,
                                                 entities=message.entities)
        split_translated_text = translated.text.split('\n')
        text = '\n'.join(split_translated_text[:-1])
        translated_info = f'\ninfo:{data["index"]}:{lang_code}'
        entities = translated.entities
        logger.debug(f'Отправляем перевод {lang_code}')
        await client.send_message(chat_id=settings.GROUP_TRANSLATE, text=text + translated_info, entities=entities)
        await asyncio.sleep(3)


@client.on_message()
async def last_filter(client: Client, message: Message):
    print('Мимо')
    # print(message.chat)
    # print(message.from_user)


try:
    client.run()
    print('Запускаем бота')
    print('Bot запущен')
except Exception as err:
    print('Ошибка при запуске бота', err)
    input('Нажмите Enter')
    raise err


