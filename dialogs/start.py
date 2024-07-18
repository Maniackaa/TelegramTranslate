import pickle
from pprint import pprint

from aiogram import Router, Bot, F
from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, Start, StubScroll, Group, NumberedPager
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger

from dialogs.states import StartSG, AddPostSG, EditTranslateSG
from services.db_func import get_last_index

router = Router()


async def start_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug('start_getter', dialog_data=data, start_data=dialog_manager.start_data)
    hello_text = f'В этом боте вы сможете '

    return {'username': event_from_user.username, 'hello_text': hello_text, 'data': data, 'media_count': 5}


async def press_add(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data
    index = get_last_index()
    data['index'] = index + 1
    await dialog_manager.start(AddPostSG.text, data=data)

start_dialog = Dialog(
    Window(
        Format(text='{hello_text}'),
        Button(
            text=Const('Добавить пост'),
            on_click=press_add,
            id='add_post'),
        state=StartSG.start,
        getter=start_getter,

    ),
)




