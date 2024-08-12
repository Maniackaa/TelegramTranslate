import json

from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import StartMode, DialogManager
from aiogram_dialog.widgets.kbd import Button

from config.bot_settings import logger
from dialogs.states import StartSG, EditTranslateSG
from services.db_func import get_or_create_post, get_or_create_translate


async def go_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)

async def next_window(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


async def get_translate(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data
    index = data.get("index")
    post = get_or_create_post(index)
    for translate in post.get_translates():
        # await bot.forward_messages(chat_id=585896156, from_chat_id=-1001960686782, message_ids=[message_id])
        raw_message = translate.raw_message
        load_message = json.loads(raw_message)
        loaded_text = load_message.get('text')
        text_without_info = '\n'.join(loaded_text.split('\n')[:-1])
        await callback.bot.send_message(chat_id=callback.from_user.id, text=text_without_info + f'\n({translate.lang_code})', entities=load_message.get('entities'))


async def to_edit_translate(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(data)
    await dialog_manager.start(EditTranslateSG.start, data=data)


async def edit_post(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    logger.debug(f'Нажата кнопка {button.text}')
    data = dialog_manager.dialog_data
    index = data.get("index")
    logger.debug(data)
    translate = get_or_create_translate(post_id=index, lang_code=data.get('lang'))
    await callback.message.answer(text=translate.html, parse_mode=ParseMode.HTML)
    await dialog_manager.switch_to(EditTranslateSG.edit)


async def save_post(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    logger.debug(f'Нажата кнопка save_post')
    data = dialog_manager.dialog_data
    logger.debug(data)
    photos = data.get('photos', [])
    photo_ids = [x[0] for x in photos]
    post = get_or_create_post(data['index'])
    post.set('photos', photo_ids)
    post.set('is_active', 1)
    await callback.answer('Рассылка Включена')


async def stop_post(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    logger.debug(f'Нажата кнопка stop_post')
    data = dialog_manager.dialog_data
    logger.debug(data)
    post = get_or_create_post(data['index'])
    post.set('is_active', 0)
    await callback.answer('Рассылка Отключена')


async def send_ready_post(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    logger.debug(f'Нажата send_ready_post')
    data = dialog_manager.dialog_data
    post = get_or_create_post(data['index'])
    print(post)
    translate = post.get_translate('ru')
    print(translate)
    if len(translate.html) >= 1000:
        await callback.bot.send_message(chat_id=callback.from_user.id, text=translate.html)
    await callback.bot.send_media_group(chat_id=callback.from_user.id, media=translate.get_media_group())
