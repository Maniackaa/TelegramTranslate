from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    start = State()


class AddPostSG(StatesGroup):
    start = State()
    text = State()
    photo = State()
    confirm = State()
    date_select = State()
    time_select = State()


class EditTranslateSG(StatesGroup):
    start = State()