import asyncio
import datetime
import json
import pickle
from typing import Sequence

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select, delete, RowMapping

from config.bot_settings import logger, settings
from database.db import Session, User, PostModel, Translate
from services.func import send_tg_message


def check_user(id):
    """Возвращает найденных пользователей по tg_id"""
    # logger.debug(f'Ищем юзера {id}')
    with Session() as session:
        user: User = session.query(User).filter(User.tg_id == str(id)).one_or_none()
        # logger.debug(f'Результат: {user}')
        return user


def get_user_from_id(pk) -> User:
    session = Session(expire_on_commit=False)
    with session:
        q = select(User).filter(User.id == pk)
        print(q)
        user = session.execute(q).scalars().one_or_none()
        return user


def get_user_from_username(username) -> User:
    session = Session(expire_on_commit=False)
    with session:
        q = select(User).filter(User.username == username)
        user = session.execute(q).scalars().one_or_none()
        return user


def get_or_create_user(user) -> User:
    """Из юзера ТГ возвращает сущестующего User ли создает его"""
    try:
        tg_id = user.id
        username = user.username
        # logger.debug(f'username {username}')
        old_user = check_user(tg_id)
        if old_user:
            # logger.debug('Пользователь есть в базе')
            return old_user
        logger.debug('Добавляем пользователя')
        with Session() as session:
            new_user = User(tg_id=tg_id,
                            username=username,
                            register_date=datetime.datetime.now()
                            )
            session.add(new_user)
            session.commit()
            logger.debug(f'Пользователь создан: {new_user}')
        return new_user
    except Exception as err:
        logger.error('Пользователь не создан', exc_info=True)


def get_last_index():
    session = Session(expire_on_commit=False)
    with session:
        index = 0
        q = select(PostModel.id).order_by(PostModel.id.desc()).limit(1)
        result = session.execute(q).scalar()
        print(result)
        if result:
            index = result
        return index


def get_or_create_post(pk):
    session = Session(expire_on_commit=False)
    with session:
        q = select(PostModel).where(PostModel.id == int(pk))
        result = session.execute(q).scalar_one_or_none()
        if not result:
            result = PostModel(id=pk)
            session.add(result)
            session.commit()
        return result


def get_or_create_translate(post_id, lang_code):
    session = Session(expire_on_commit=False)
    with session:
        q = select(Translate).where(Translate.post_id == int(post_id)).where(Translate.lang_code == lang_code)
        result = session.execute(q).scalar_one_or_none()
        if not result:
            result = Translate(post_id=int(post_id), lang_code=lang_code)
            session.add(result)
            session.commit()
        logger.debug(f'get_or_create_translate {post_id} {lang_code}: {result.id}')
        return result


def get_posts_to_send(send_type='group'):
    #  Посты в группу
    session = Session(expire_on_commit=False)
    now = settings.tz.localize(datetime.datetime.now())
    with session:
        q = select(PostModel).where(PostModel.posted_time == None).where(
            PostModel.is_active == 1).where(
            PostModel.target_time <= now).where(PostModel.type == send_type)
        result = session.execute(q).scalars().all()
        return result


async def main():
    pass
    # user = get_user_from_id(1)
    # x = get_or_create_post('1')
    # post = get_or_create_post(82)
    # print(post)
    # translated_post = post.get_translate('en')
    # for t in post.get_translates():
    #     raw_message = t.raw_message
    #     json.loads(raw_message)

    posts = get_posts_to_send()
    print(posts)
    # post = posts[-1]
    # for translate in post.get_translates():
    #     print()
    #     print(translate.id, translate.post.id)
    #     raw_message = translate.raw_message
    #     print(raw_message)
    #     load_message = json.loads(raw_message)
    #     print(load_message)
    #     loaded_text = load_message.get('text')
    #     entities = load_message.get('entities')
    #     text_without_info = '\n'.join(loaded_text.split('\n')[:-1])
    #     print(text_without_info)
    #     print(entities)
    #     bot = Bot(token=settings.BOT_TOKEN)
    #     await bot.send_message(chat_id=settings.ADMIN_IDS[0], text=text_without_info, entities=load_message.get('entities'))
    #     # await send_tg_message(ids_to_send=settings.ADMIN_IDS, text=translate.get_json_message()['text'],
    #     #                       entities=translate.get_json_message().get('entities'))



if __name__ == '__main__':
    asyncio.run(main())
#
