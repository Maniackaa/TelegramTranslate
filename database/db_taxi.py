from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.bot_settings import settings

db_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(db_url, echo=True)
Session = sessionmaker(bind=engine)

session = Session(expire_on_commit=False)


def get_bot_users():
    # [(357007142, 'zh'), (357007142, 'uz'),...
    with engine.connect() as connection:
        result = connection.execute(text(
            """SELECT telegram_id, language_code FROM users join languages ON language_id;"""
        ))
        return result.all()
