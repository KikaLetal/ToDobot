from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import app.DataBase as db

mainMenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить задачу"), KeyboardButton(text="Изменить задачу")],
        [KeyboardButton(text="Удалить задачу"), KeyboardButton(text="Статус задачи")],
        [KeyboardButton(text="Показать задачи"), KeyboardButton(text="Сообщить об ошибке")],
    ],
    resize_keyboard=True
)

cancel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/Отмена")]
    ],
    resize_keyboard=True
)

status = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="To Do 📝"),
            KeyboardButton(text="In progress ⏳"),
            KeyboardButton(text="Done ✅"),
         ]
    ],
    resize_keyboard=True
)

async def inline_tasks(tasks : list[db.Task] = None, next_page:bool = True, page :int = 0):
    keyboard = InlineKeyboardBuilder()
    if tasks:
        for task in tasks:
            keyboard.row(
                InlineKeyboardButton(
                    text=task.text,
                    callback_data=f"choise:{task.id}"
                )
            )
    nav_buttons = []
    if page != 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Предыдущая страница",
                callback_data=f"page:{page-1}"
            )
        )
    if next_page:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Следующая страница",
                callback_data=f"page:{page+1}"
            )
        )

    if nav_buttons:
        keyboard.row(*nav_buttons)

    keyboard.row(
            InlineKeyboardButton(
                text="Вернуться",
                callback_data=f"exit"
            )
        )
    return keyboard.as_markup()