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

from dialogs.states import StartSG, AddPostSG, EditTranslateSG


async def edit_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    post = bd_data['11258']
    logger.debug(post)
    langs = list(post.keys())
    items = []
    for item in langs:
        items.append((item, item))
    print(items)
    result = {'post': post,
              'preview': data.get('preview', f'Переведено {len(langs) - 1}/{len(settings.LANG_CODES)}'),
              "media_count": len(langs),
              'items': items,
              'lang': data.get('lang')
              }
    return result


async def sel_translate(callback: CallbackQuery, widget: Select,
                         dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    post = bd_data['11258']
    lang_post = post[item_id]
    # message_raw = lang_post['message']
    # message = json.loads(message_raw)
    data.update(preview=lang_post['html'])
    data.update(lang=item_id)


async def see_post(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.dialog_data
    post = bd_data['11258']
    if data.get('last_msg'):
        msg = data.get('last_msg')
        await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=msg.message_id)
    lang = data['lang']
    lang_post = post[lang]
    message_raw = lang_post['message']
    message = json.loads(message_raw)
    last_msg = await callback.bot.send_message(chat_id=callback.from_user.id, text=message['text'], entities=message['entities'])
    data.update(last_msg=last_msg)

edit_translate_dialog = Dialog(
    Window(
        Format(text='{preview}'),
        Button(text=Const('Показать перевод'),
               id='see_post',
               on_click=see_post,
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
)

