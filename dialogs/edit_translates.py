import asyncio
import datetime
import json
import pickle
from pprint import pprint

from aiogram import Router, Bot, F
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, StubScroll, Group, NumberedPager, \
    SwitchTo, Start, Calendar, Cancel
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger
from database.db import bd_data
from dialogs.buttons import edit_post

from dialogs.states import StartSG, AddPostSG, EditTranslateSG
from services.db_func import get_or_create_post, get_or_create_translate


async def edit_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(data)
    data.update(**dialog_manager.start_data)
    logger.debug(data)
    index = data.get("index")
    post = get_or_create_post(index)
    logger.debug(post)
    langs = settings.CHANNEL_CODES.keys()
    items = []
    for item in settings.CHANNEL_CODES:
        items.append((item, item))
    result = {'post': post,
              'preview': data.get('preview', f'Переведено {len(post.get_translates())}/{len(langs)}'),
              "media_count": len(langs),
              'items': items,
              'lang': data.get('lang')
              }
    return result


async def sel_translate(callback: CallbackQuery, widget: Select,
                         dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    index = data.get("index")
    post = get_or_create_post(index)
    logger.debug(f'post: {post}, item_id: {item_id}')
    translated_post = post.get_translate(item_id)
    logger.debug(f'translated_post: {translated_post}')
    # message_raw = lang_post['message']
    # message = json.loads(message_raw)
    data.update(preview=translated_post.text)
    data.update(lang=item_id)


async def see_post(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    index = data.get("index")
    post = get_or_create_post(index)
    if data.get('last_msg'):
        msg = data.get('last_msg')
        try:
            await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=msg.message_id)
        except Exception as err:
            pass
    lang = data['lang']
    logger.debug(f'lang: {lang}')
    translated_post = post.get_translate(lang)
    message_raw = translated_post.raw_message
    json_msg = json.loads(message_raw)
    last_msg = await callback.bot.send_message(chat_id=callback.from_user.id, text=json_msg.get('text', 'No text'),
                                               entities=json_msg.get('entities', []))
    data.update(last_msg=last_msg)


async def insert_edited_post(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str, *args, **kwargs) -> None:
    data = dialog_manager.dialog_data
    logger.debug(f'Вставлен новый перевод. Index: {data.get("index")} lang: {data.get("lang")}')
    logger.debug(data)
    translate = get_or_create_translate(data.get('index'), data.get('lang'))
    translate.set('text', message.text)
    translate.set('html', message.html_text)
    translate.set('raw_message', message.model_dump_json(exclude_defaults=True, exclude_none=True))


edit_translate_dialog = Dialog(
    Window(
        Format(text='{preview}'),
        Button(text=Const('Показать перевод'),
               id='see_post',
               on_click=see_post,
               when='lang'
               ),
        Button(text=Const('Изменить перевод'),
               id='change_post',
               on_click=edit_post,
               when='lang'
               ),
        Group(
            Select(Format('{item[0]}'),
                   id='sel_translate',
                   on_click=sel_translate,
                   items='items',
                   item_id_getter=lambda x: x[1]),
            width=4,
        ),
        Cancel(Const('Назад')),
        state=EditTranslateSG.start,
        getter=edit_getter
    ),
    Window(
        Format(text='Вставьте новый текст'),
        TextInput(
            id='edit_translate',
            on_success=insert_edited_post,
        ),
        Cancel(Const('Назад')),
        state=EditTranslateSG.edit,
        getter=edit_getter
    ),
)

