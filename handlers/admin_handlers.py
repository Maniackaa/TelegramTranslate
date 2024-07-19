import datetime
import json
from pathlib import Path


from aiogram import Bot, F, Router
from aiogram.filters import (ADMINISTRATOR, KICKED, LEFT, MEMBER,
                             ChatMemberUpdatedFilter, Command, StateFilter, BaseFilter, CommandStart, CommandObject)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (CallbackQuery, ChatInviteLink, ChatMemberUpdated,
                           InlineKeyboardButton, Message, FSInputFile)
from aiogram_dialog import DialogManager, StartMode, ShowMode


from config.bot_settings import BASE_DIR, settings
from dialogs.add_post import add_post_dialog
from dialogs.edit_translates import edit_translate_dialog
from dialogs.start import start_dialog
from dialogs.states import StartSG
from keyboards.keyboards import custom_kb

from config.bot_settings import logger
from services.db_func import get_or_create_user


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        self.admins = settings.ADMIN_IDS

    async def __call__(self, message: Message) -> bool:
        result = message.from_user.id in self.admins
        print(f'Проверка на админа\n'
              f'{message.from_user.id} in {self.admins}: {result}')
        return result


router: Router = Router()
router.include_router(start_dialog)
router.include_router(add_post_dialog)
router.include_router(edit_translate_dialog)


@router.message(CommandStart(deep_link=True))
async def handler(message: Message, command: CommandObject, bot: Bot, dialog_manager: DialogManager):
    user = get_or_create_user(message.from_user)
    args = command.args
    # payload = decode_payload(args)
    logger.debug(f'payload: {args}')
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND, data={'org_key': args})


@router.message(CommandStart())
async def command_start_process(message: Message, bot: Bot, dialog_manager: DialogManager):
    user = get_or_create_user(message.from_user)
    logger.info('Старт', user=user, channel=message.chat.id)
    # await message.answer('Привет', reply_markup=start_kb)
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)


@router.callback_query(F.data == 'start_test')
async def start_test(callback: CallbackQuery, state: FSMContext):
    user = get_or_create_user(callback.from_user)
    logger.info('Старт', user=user)


