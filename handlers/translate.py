from aiogram import Router, Bot, F
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.db import bd_data
from services.db_func import get_or_create_translate
from services.func import get_data_from_info_string, get_info_string_from_message

router: Router = Router()
from config.bot_settings import logger, settings


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        self.admins = settings.ADMIN_IDS

    async def __call__(self, message: Message) -> bool:
        result = message.from_user.id in self.admins
        print(f'Проверка на админа\n'
              f'{message.from_user.id} in {self.admins}: {result}')
        return result


class ToTranslate(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text:
            result = 'info:' in message.text
            return result
#
# def get_data_from_info_string(info: str) -> dict:
#     # info:137:ru
#     splitted = info.split(':')
#     index = splitted[1]
#     lang_code = splitted[2]
#     return {
#         'index': index,
#         'lang_code': lang_code
#     }


# def get_info_string_from_message(text: str):
#     split = text.split('\n')
#     info_string = split[-1]
#     if info_string.startswith('info:'):
#         return info_string

# @router.edited_message()
# async def edit_message(message: Message, state: FSMContext, bot: Bot):
#     logger.info(f'Редактирование сообщения: {message.text}')
#     info_string = get_info_string_from_message(message.text)
#     data = get_data_from_info_string(info_string)
#     lang_code = data['lang_code']
#     index = data['index']
#     bd_data[index][lang_code] = {'msg_id': message.message_id, 'message': message.model_dump_json()}
#
#
# @router.message(Command('send'))
# async def sender(message: Message, state: FSMContext, bot: Bot):
#     logger.info(f'Начинаем рассылку: {bd_data}')
#     data = bd_data.get('112')
#     for lang_code, message_data in data.items():
#         # await bot.forward_messages(chat_id=585896156, from_chat_id=-1001960686782, message_ids=[message_id])
#         print(lang_code)
#         print(message_data)
#         # await bot.copy_message(chat_id=585896156, from_chat_id=-1001960686782, message_id=message_data['msg_id'])
#         dump_message = message_data['message']
#         load_message = json.loads(dump_message)
#         loaded_text = load_message.get('text')
#         text_without_info = '\n'.join(loaded_text.split('\n')[:-1])
#         await bot.send_message(chat_id=585896156, text=text_without_info, entities=load_message.get('entities'))
#
#
# # Прием оригнального сообщения и отправка на перевод
# @router.message(ToTranslate(), IsAdmin(), F.chat.type == 'private', F.chat.id == 585896156)
# async def receive_original(message: Message, state: FSMContext, bot: Bot):
#     print('ok')
#     index = '11258'
#     text = f'{message.text}\ninfo:{index}:ru'
#     msg = await bot.send_message(chat_id=-1001960686782, text=text, entities=message.entities)
#     bd_data[index] = {'ru': {'msg_id': msg.message_id, 'message': msg.model_dump_json()}}
#     # await message.answer(text=message.text, entities=message.entities)


# Прием переведенных сообщений
@router.message(ToTranslate(), IsAdmin(), F.chat.id == settings.GROUP_TRANSLATE)
async def receive_translated(message: Message, state: FSMContext, bot: Bot):
    logger.info(f'Принят перевод: {logger.debug(message)}')
    info_string = get_info_string_from_message(message.text)
    logger.info(f'info_string: {info_string}')
    data = get_data_from_info_string(info_string)
    logger.info(f'data: {data}')
    # msg = await bot.send_message(chat_id=585896156, text=message.text, entities=message.entities)
    lang_code = data['lang_code']
    index = data['index']
    # bd_data[index][lang_code] = {'msg_id': message.message_id, 'message': message.model_dump_json(), 'html': message.html_text}
    # print(bd_data)
    translate = get_or_create_translate(post_id=index, lang_code=lang_code)
    logger.debug(f'translate: {translate.id}')
    translate.set('channel_id', settings.CHANNEL_CODES[lang_code])
    translate.set('text', message.text)
    translate.set('html', message.html_text)
    translate.set('raw_message', message.model_dump_json(exclude_defaults=True, exclude_none=True))


# @router.message()
# async def echo(message: Message, state: FSMContext, bot: Bot):
#     print('echo')
#     print(message.chat.type)
#     print(message.chat.id, type(message.chat.id))