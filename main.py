import asyncio
import datetime
import json
import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, ErrorEvent, ReplyKeyboardRemove, \
    FSInputFile, BufferedInputFile
from aiogram_dialog import setup_dialogs, StartMode, ShowMode, DialogManager
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.bot_settings import logger, settings
from database.db_taxi import get_bot_users
from dialogs.states import StartSG
from handlers import admin_handlers, translate, action_handlers
from services.db_func import get_posts_to_send


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
    logger.debug('Запуск рассыльщика в группу')
    posts = get_posts_to_send()
    for post in posts:
        for post_translate in post.get_translates():
            try:
                raw_message = post_translate.raw_message
                load_message = json.loads(raw_message)
                loaded_text = load_message.get('text')
                entities = load_message.get('entities')
                text_without_info = '\n'.join(loaded_text.split('\n')[:-1])
                bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
                # await bot.send_media_group(chat_id=settings.ADMIN_IDS[1], media=translate.get_media_group())
                await bot.send_media_group(chat_id=post_translate.channel_id, media=post_translate.get_media_group())
                await asyncio.sleep(1)
            except Exception as err:
                logger.error(err)
        post.set('posted_time', datetime.datetime.now())
        post.set('is_active', 0)


async def bot_post_sender():
    logger.debug('Запуск рассыльщика по боту')
    posts = get_posts_to_send('bot')
    logger.debug(f'to send bot: {posts}')
    users_to_send = get_bot_users()
    # print(users_to_send)
    # users_to_send = [('585896156', 'ru'), ('585896156', 'en')]
    bot_taxi = Bot(token=settings.TAXIBOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    for post in posts:
        taxi_photo_ids = []
        await bot_taxi.send_message(chat_id=settings.ADMIN_IDS[0], text='Преобразуем фото для бота такси')
        for photo_id in post.photos:
            d = await bot.download(file=photo_id)
            photo_bytes = d.read()
            msg = await bot_taxi.send_photo(chat_id=settings.ADMIN_IDS[0],
                                            photo=BufferedInputFile(photo_bytes, filename=photo_id))
            taxi_photo_id = msg.photo[-1].file_id
            taxi_photo_ids.append(taxi_photo_id)
        for user_tg, lang_code in users_to_send:
            await asyncio.sleep(0.05)
            try:
                pass
                post_translate = post.get_translate(lang_code)
                if post_translate:
                    logger.debug(f'send to: {user_tg}')
                    msg = await bot_taxi.send_media_group(chat_id=user_tg,
                                                          media=post_translate.get_media_group_for_taxi(taxi_photo_ids))

            except Exception as err:
                logger.error(f'Ошибка при отправке юзеру {user_tg} {post.id} {lang_code}: {err}')

        post.set('posted_time', datetime.datetime.now())
        post.set('is_active', 0)


def set_scheduled_jobs(scheduler, *args, **kwargs):
    scheduler.add_job(post_sender, "interval", seconds=60)
    scheduler.add_job(bot_post_sender, "interval", seconds=60)


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
