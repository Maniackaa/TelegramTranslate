import dataclasses
import datetime
import json
import pickle

from aiogram.types import Message
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import create_engine, ForeignKey, String, DateTime, \
    Integer, select, delete, Text, BLOB, JSON


from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


# db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
from config.bot_settings import BASE_DIR, logger, settings

db_path = BASE_DIR / 'base.sqlite'
db_url = f"sqlite:///{db_path}"
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    def set(self, key, value):
        _session = Session(expire_on_commit=False)
        with _session:
            setattr(self, key, value)
            _session.add(self)
            _session.commit()
            logger.debug(f'Изменено значение {key} на {value}')
            return self


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(30), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    fio: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=0)
    balance: Mapped[int] = mapped_column(Integer(), default=150)
    # objs: Mapped[list['ObjModel']] = relationship(back_populates='user', lazy='subquery')

    def __repr__(self):
        return f'{self.id}. {self.username or "-"} {self.tg_id}'


class PostModel(Base):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    # user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    # user: Mapped['User'] = relationship(back_populates='objs', lazy='subquery')
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(tz=settings.tz))
    text: Mapped[str] = mapped_column(String(4000), default='')
    html: Mapped[str] = mapped_column(String(4000), default='')
    raw_message: Mapped[json] = mapped_column(JSON(), nullable=True)
    # msg = Message(**json.loads(request.msg))
    # msg = Message.model_validate(msg).as_(bot)
    photos: Mapped[str] = mapped_column(JSON(),nullable=True)
    target_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    translates: Mapped[list['Translate']] = relationship(back_populates='post', lazy='select')
    is_active: Mapped[int] = mapped_column(Integer(), default=0)

    def validate_message(self, bot):
        msg = Message(**json.loads(self.raw_message))
        return Message.model_validate(msg).as_(bot)

    def get_translates(self):
        _session = Session(expire_on_commit=False)
        with _session:
            q = select(Translate).where(Translate.post_id == self.id)
            result = _session.execute(q).scalars().all()
            return result

    def get_translate(self, lang_code):
        _session = Session(expire_on_commit=False)
        with _session:
            logger.debug(f'Ищем перевод поста {self.id} lang {lang_code}')
            q = select(Translate).where(Translate.post_id == self.id, Translate.lang_code == lang_code)
            result = _session.execute(q).scalar_one_or_none()
            return result

    def __str__(self):
        return f'{self.__class__.__name__}({self.id})'


class Translate(Base):
    __tablename__ = 'translates'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey('posts.id', ondelete='CASCADE'))
    post: Mapped['PostModel'] = relationship(back_populates='translates', lazy='subquery')
    lang_code: Mapped[str] = mapped_column(String(10), nullable=True)
    channel_id: Mapped[int] = mapped_column(Integer(), nullable=True)
    text: Mapped[str] = mapped_column(String(4000), nullable=True)
    html: Mapped[str] = mapped_column(String(4000), nullable=True)
    raw_message: Mapped[json] = mapped_column(JSON(), nullable=True)

    def get_media_group(self):
        text_without_info = '\n'.join(self.html.split('\n')[:-1])
        media_group = MediaGroupBuilder(caption=text_without_info)
        for photo in self.post.photos:
            media_group.add_photo(media=photo)
        return media_group.build()
    def get_json_message(self):
        json_msg = json.loads(self.raw_message)
        return json_msg

    def __str__(self):
        return f'{self.__class__.__name__}({self.id}. Post {self.post_id} "{self.lang_code}")'


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(engine)
bd_data = {}