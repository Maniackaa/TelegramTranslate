import datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER, LEFT, ADMINISTRATOR, KICKED
from aiogram.types import CallbackQuery, Message, ChatInviteLink, \
    InlineKeyboardButton, ChatMemberUpdated, ChatJoinRequest, FSInputFile

from config.bot_settings import logger


router: Router = Router()


# Действия юзеров
@router.chat_join_request()
async def approve_request(chat_join: ChatJoinRequest, bot: Bot):
    logger.debug('chat_join')
    logger.debug(str(chat_join))


# Действия юзеров
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=LEFT))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_kick(event: ChatMemberUpdated, bot: Bot):
    logger.debug('USER KICKED or LEFT')
    logger.debug(str(event))


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_join(event: ChatMemberUpdated, bot: Bot, *args, **kwargs):
    logger.debug('USER MEMBER')
    logger.debug(str(event))


# Действия бота
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def as_member(event: ChatMemberUpdated, bot: Bot, *args, **kwargs):
    logger.debug('MY event MEMBER')
    logger.debug(str(event))


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(LEFT | KICKED)))
async def left(event: ChatMemberUpdated, bot: Bot):
    logger.debug('MY event LEFT')
    logger.debug(str(event))


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
async def as_admin(event: ChatMemberUpdated, bot: Bot):
    logger.debug('MY event ADMINISTRATOR')
    logger.debug(str(event))