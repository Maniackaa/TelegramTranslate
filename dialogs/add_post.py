import asyncio
import datetime
import json
import pickle
from pprint import pprint

from aiogram import Router, Bot, F
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, Update, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog import Dialog, Window, DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput, TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Url, Column, Back, Next, StubScroll, Group, NumberedPager, \
    SwitchTo, Start, Calendar
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format, Const

from config.bot_settings import settings, logger
from database.db import bd_data

from dialogs.states import StartSG, AddPostSG, EditTranslateSG
from dialogs.type_factorys import positive_int_check, tel_check, time_check


async def new_post_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    data.update(dialog_manager.start_data)
    result = {}
    # for key, values in car_data.items():
    #     items = []
    #     for index, item in enumerate(values):
    #         items.append((index, item))
    #     result[f'{key}_items'] = items
    # data['getter'] = result
    photos = data.get('photos', [])
    photo_count = len(photos)
    result['photo_count'] = photo_count
    # logger.debug(data)
    return result


async def result_getter(dialog_manager: DialogManager, event_from_user: User, bot: Bot, event_update: Update, **kwargs):
    data = dialog_manager.dialog_data
    logger.debug(f'{data}')
    return {}


async def item_select(callback: CallbackQuery, widget: Select,
                       dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.dialog_data
    getter = data['getter']
    field = widget.widget_id
    data[f'{field}_id'] = item_id
    data[f'{field}_str'] = getter[f'{field}_items'][int(item_id)][1]
    await dialog_manager.next()
    logger.debug(f'data: {data}')


async def text_input(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str, *args, **kwargs) -> None:
    data = dialog_manager.dialog_data
    field = widget.widget.widget_id
    data[field] = text
    if field == 'text':
        data['entities'] = message.entities
        await message.bot.send_message(chat_id=message.from_user.id, text=data['text'], entities=data.get('entities', []))
        msg = await message.bot.send_message(chat_id=-1001960686782, text=f'{text}\ninfo:{11258}:ru', entities=data.get('entities', []))
        # await message.bot.send_message(chat_id=message.from_user.id, text=data['text'])
        # msg = await message.bot.send_message(chat_id=-1001960686782, text=f'{text}\ninfo:{11258}:ru',)
        bd_data['11258'] = {'ru': {'msg_id': msg.message_id, 'message': msg.model_dump_json(), 'html': message.html_text}}
    await dialog_manager.next()
    logger.debug(f'data: {data}')

    print(message.html_text)
    await message.answer(text=message.html_text, parse_mode=ParseMode.HTML)


async def photo_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager) -> None:
    # await message.send_copy(message.chat.id)
    print(message.content_type)
    data = dialog_manager.dialog_data
    photos = data.get('photos', [])
    photos.append((message.photo[-1].file_id, message.photo[-1].file_unique_id))
    photos = photos[-10:]
    data['photos'] = photos


async def on_delete(
        callback: CallbackQuery, widget: Button, dialog_manager: DialogManager,
):
    scroll: ManagedScroll = dialog_manager.find("pages")
    media_number = await scroll.get_page()
    photos = dialog_manager.dialog_data.get("photos", [])
    del photos[media_number]
    if media_number > 0:
        await scroll.set_page(media_number - 1)


async def get_photos(dialog_manager: DialogManager, event_from_user, **kwargs):
    is_admin = event_from_user.id in settings.ADMIN_IDS
    scroll: ManagedScroll = dialog_manager.find("pages")
    media_number = await scroll.get_page()
    photos = dialog_manager.dialog_data.get("photos", [])
    if photos:
        photo = photos[media_number]
        media = MediaAttachment(
            file_id=MediaId(*photo),
            type=ContentType.PHOTO,
        )
    else:
        media = MediaAttachment(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Image_not_available.png/800px-Image_not_available.png?20210219185637",  # noqa: E501
            type=ContentType.PHOTO,
        )
    data = dialog_manager.dialog_data
    data['media'] = media
    return {
        "media_count": len(photos),
        "media_number": media_number + 1,
        "media": media,
        "text1": data['text'],
        "is_admin": is_admin
    }


# async def send_obj(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
#     data = dialog_manager.dialog_data
#     logger.debug(data)
#     # selected_date = data['selected_date']
#     # time_select = data['time_select']
#     # time = datetime.datetime.strptime(time_select, '%H:%M').time()
#     # start_send = settings.tz.localize(
#     #     datetime.datetime.combine(
#     #         selected_date,
#     #         time,
#     #     )
#     # )
#     text = data['text']
#     await callback.bot.send_message(chat_id=callback.from_user.id, text=data['text'], entities=data.get('entities', []))
#
#     msg = await callback.bot.send_message(chat_id=-1001960686782, text=f'{text}\ninfo:{11258}:ru', entities=data.get('entities', []))
#     bd_data['11258'] = {'ru': {'msg_id': msg.message_id, 'message': msg.model_dump_json()}}


async def on_date_selected(callback: CallbackQuery, widget,
                           dialog_manager: DialogManager, selected_date: datetime.date):
    await callback.answer(str(selected_date))
    data = dialog_manager.dialog_data
    data.update(selected_date=selected_date)
    await dialog_manager.next()


async def get_translate(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, *args, **kwargs):
    data = dialog_manager.dialog_data
    print(bd_data)
    post = bd_data.get('11258')
    for lang_code, message_data in post.items():
        # await bot.forward_messages(chat_id=585896156, from_chat_id=-1001960686782, message_ids=[message_id])
        print(lang_code)
        print(message_data)
        # await bot.copy_message(chat_id=585896156, from_chat_id=-1001960686782, message_id=message_data['msg_id'])
        dump_message = message_data['message']
        load_message = json.loads(dump_message)
        loaded_text = load_message.get('text')
        text_without_info = '\n'.join(loaded_text.split('\n')[:-1])
        await callback.bot.send_message(chat_id=callback.from_user.id, text=text_without_info + f'\n({lang_code})', entities=load_message.get('entities'))


add_post_dialog = Dialog(
    Window(
        Format(text='Вставьте текст поста'),
        TextInput(
            id='text',
            on_success=text_input,
        ),
        Back(Const('Назад')),
        state=AddPostSG.text,
    ),
    Window(
        Format(text='Выберите дату'),
        Calendar(id='date_select', on_click=on_date_selected),
        state=AddPostSG.date_select
    ),
    Window(
        Format(text='Укажите время в формате 03:50'),
        TextInput(
            id='time_select',
            on_success=text_input,
            type_factory=time_check,
        ),
        Back(Const('Назад')),
        state=AddPostSG.time_select,
    ),
    Window(
        Const(text='9️⃣ Отправьте до 10 фото, затем нажмите далее'),
        Format(text='Добавлено {photo_count} фото'),
        MessageInput(
            func=photo_handler,
            content_types=ContentType.PHOTO,
        ),
        Back(Const('Назад')),
        Next(Const('Далее')),
        state=AddPostSG.photo,
        getter=new_post_getter,
    ),
    Window(
        Format(text='{text1}'),
        DynamicMedia(selector="media"),
        StubScroll(id="pages", pages="media_count"),
        Group(
            NumberedPager(scroll="pages", when=F["pages"] > 1),
            width=5,
        ),
        Button(
            Format("🗑️ Удалить фото #{media_number}"),
            id="del",
            on_click=on_delete,
            when="media_count",
            # Alternative F['media_count']
        ),
        Back(Const('Назад')),
        # Button(text=Const('Готово'),
        #        id='send_obj_btn',
        #        on_click=send_obj,
        #        when='media_count'
        #        ),
        # Button(text=Const('Выполнить перевод'),
        #        id='send_obj_now',
        #        on_click=send_obj,
        #        when='is_admin'
        #        ),
        Button(text=Const('Прислать переводы'),
               id='get_taranslate',
               on_click=get_translate,
               when='is_admin'
               ),
        Start(text=Const('Редактировать переводы'),
              id='edit_taranslate',
              state=EditTranslateSG.start,
              when='is_admin',
              ),
        Start(text=Const('Заново'), state=StartSG.start, id='start'),
        state=AddPostSG.confirm,
        getter=get_photos,
    ),
)
