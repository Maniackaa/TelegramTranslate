import asyncio
import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, ErrorEvent, ReplyKeyboardRemove
from aiogram_dialog import setup_dialogs, StartMode, ShowMode, DialogManager
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.bot_settings import logger, settings
from dialogs.states import StartSG
from handlers import admin_handlers, translate, action_handlers


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description="Start",
        ),
    ]

    admin_commands = commands.copy()
    admin_commands.append(
        BotCommand(
            command="admin",
            description="Admin panel",
        )
    )

    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(
                    chat_id=admin_id,
                ),
            )
        except Exception as err:
            logger.info(f'Админ id {admin_id}  ошибочен')


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    # Example of handling UnknownIntent Error and starting new dialog.
    logger.error("Restarting dialog: %s", event.exception)
    if event.update.callback_query:
        await event.update.callback_query.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
        )
        if event.update.callback_query.message:
            try:
                await event.update.callback_query.message.delete()
            except TelegramBadRequest:
                pass  # whatever
    elif event.update.message:
        await event.update.message.answer(
            "Bot process was restarted due to maintenance.\n"
            "Redirecting to main menu.",
            reply_markup=ReplyKeyboardRemove(),
        )
    await dialog_manager.start(
        StartSG.start,
        mode=StartMode.NORMAL,
        show_mode=ShowMode.SEND,
    )


async def on_unknown_state(event, dialog_manager: DialogManager):
    # Example of handling UnknownState Error and starting new dialog.
    logger.error(f"Restarting dialog: {event.exception}")
    await dialog_manager.start(
        StartSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,
    )


async def post_sender():
    logger.debug('Запуск рассыльщика')



def set_scheduled_jobs(scheduler, *args, **kwargs):
    scheduler.add_job(post_sender, "interval", seconds=60)


async def main():

    if settings.USE_REDIS:
        storage = RedisStorage.from_url(
            url=f"redis://{settings.REDIS_HOST}",
            connection_kwargs={
                "db": 0,
            },
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    # bot = Bot(token=settings.BOT_TOKEN,  default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())

    try:
        dp.include_router(translate.router)
        dp.include_router(admin_handlers.router)
        dp.include_router(action_handlers.router)
        dp.errors.register(on_unknown_intent, ExceptionTypeFilter(UnknownIntent), )
        setup_dialogs(dp)

        await set_commands(bot)
        # await bot.get_updates(offset=-1)
        await bot.delete_webhook(drop_pending_updates=True)

        await bot.send_message(chat_id=settings.ADMIN_IDS[0], text='Бот запущен')

        scheduler = AsyncIOScheduler()
        set_scheduled_jobs(scheduler)
        scheduler.start()

        # await bot.send_message(chat_id=config.tg_bot.GROUP_ID, text='Бот запущен', reply_markup=begin_kb)
        await dp.start_polling(bot, config=settings)
    finally:
        await dp.fsm.storage.close()
        await bot.session.close()


try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    logger.error("Bot stopped!")
