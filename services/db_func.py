import asyncio
import datetime
import json
import pickle
from typing import Sequence

from sqlalchemy import select, delete, RowMapping

from config.bot_settings import logger, settings
from database.db import Session, User, PostModel, Translate


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
        q = select(Translate).where(Translate.id == int(post_id), Translate.lang_code == lang_code)
        result = session.execute(q).scalar_one_or_none()
        if not result:
            result = Translate(post_id=post_id, lang_code=lang_code)
            session.add(result)
            session.commit()
        return result


async def main():
    pass
    # user = get_user_from_id(1)
    # x = get_or_create_post('1')
    post = get_or_create_post(42)
    print(post)
    translated_post = post.get_translate('en')
    print(translated_post)
    print(translated_post.text)

if __name__ == '__main__':
    asyncio.run(main())
#
