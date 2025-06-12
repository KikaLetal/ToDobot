from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import app.DataBase as db
import app.keyboards as kb
from sqlalchemy import select
from config import IDForDebugMessage


router = Router()

def RegisterHandlers(bot):
    class Task(StatesGroup):
        task = State()

    class EditTask(StatesGroup):
        task = State()

    class EditStatus(StatesGroup):
        status = State()

    class DebugMessage(StatesGroup):
        text = State()

    class Action(StatesGroup):
        action = State()

    # cancel
    @router.message(F.text == "/Отмена")
    async def CancelDebugMessage(message: Message, state: FSMContext):
        await message.answer("Действие отменено ⚠️❌",
                             reply_markup=kb.mainMenu)
        await state.clear()

    #pagination
    async def GetPages(user_id:int, page:int, page_size:int) -> list[db.Task]:
        offset = page * page_size
        limit = page_size + 1
        async with db.AsyncSession() as session:
            stmt = (
                select(db.Task)
                .where(db.Task.user_id == user_id)
                .limit(limit)
                .offset(offset)
            )
            data = await session.execute(stmt)
            return data.scalars().all()

    #render pages
    async def RenderPages(user_id:int, page:int = 0, page_size:int = 10) -> tuple[str, bool, list[db.Task]]:
        data = await GetPages(user_id=user_id, page=page, page_size=page_size)
        tasks = ""

        for iter, task in enumerate(data[:page_size], start=1+ page * page_size):
            tasks += f"📃 Task {iter}:  {task.text} | {task.status}\n\n"

        return tasks or "задач пока нет 🥺", len(data) > page_size, data[:page_size]

    #exit callback
    @router.callback_query(F.data == "exit")
    async def handleExitCallback(callback: CallbackQuery, state: FSMContext):
        await callback.message.delete()
        await callback.message.answer(
            "Возврат в главное меню",
            reply_markup=kb.mainMenu
        )
        await state.clear()
        await callback.answer()

    #paging callback
    @router.callback_query(F.data.startswith("page:"))
    async def handlePageCallback(callback: CallbackQuery, state: FSMContext):
        page = int(callback.data.split(":")[1])
        state_name = await state.get_state()
        text, IsNextPage, tasks = await RenderPages(user_id=callback.from_user.id, page=page)
        if state_name == Action.action:
            keyboard = await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=page)
        else:
            keyboard = await kb.inline_tasks(next_page=IsNextPage, page=page)
        await callback.message.edit_text(
            text,
            reply_markup=keyboard
        )
        await callback.answer()

    #action callback
    @router.callback_query(F.data.startswith("choise:"))
    async def handleActionCallback(callback: CallbackQuery, state: FSMContext):
        Task_ID = int(callback.data.split(":")[1])
        data = await state.get_data()
        action = data.get("action")
        if action == "edit":
            await state.set_state(EditTask.task)
            await callback.message.answer("Введите задачу ✏️", reply_markup=kb.cancel)
            await state.update_data(taskID= Task_ID)
            await callback.message.delete()
        elif action == "delete":
            async with db.AsyncSession() as session:
                stmt = (
                    select(db.Task)
                    .where(db.Task.id == Task_ID)
                )
                result = await session.execute(stmt)
                task = result.scalars().first()

                if task:
                    await session.delete(task)
                    await session.commit()
            text, IsNextPage, tasks = await RenderPages(user_id=callback.from_user.id, page=0)
            await callback.message.edit_text(text, reply_markup=await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=0))

        elif action == "status":
            await state.set_state(EditStatus.status)
            await state.update_data(taskID= Task_ID)
            sent_msg = await callback.message.answer("Выберите новый статус ✏️", reply_markup=kb.status)
            await state.update_data(messageID= sent_msg.message_id)
            await callback.message.delete()

        await callback.answer()
    #/start
    @router.message(CommandStart())
    async def cmd_start(message: Message):
        await message.answer("Вас приветствует pet-проект ToDo листа 👋👋👋",
                             reply_markup=kb.mainMenu)

    #adding tasks
    @router.message(F.text == "Добавить задачу")
    async def AddTask(message: Message, state: FSMContext):
        await state.set_state(Task.task)
        await message.answer("Введите задачу ✏️", reply_markup=kb.cancel)

    @router.message(Task.task, ~F.text)
    async def WrongTaskText(message: Message, state: FSMContext):
        await message.answer("Неверный ввод, ожидалось текстовое сообщение ⚠️❌",
                             reply_markup=kb.mainMenu)
        await state.clear()

    @router.message(Task.task)
    async def GetTaskText(message: Message, state: FSMContext):
        await state.update_data(task=message.text)
        data = await state.get_data()
        async with db.AsyncSession() as session:
            task = db.Task(user_id= message.from_user.id, text=data["task"])
            session.add(task)
            await session.commit()
        await message.answer(f"задача {data['task']}, успешно сохранена 🎉✅",
                             reply_markup=kb.mainMenu)
        await state.clear()

    #show all tasks
    @router.message(F.text == "Показать задачи")
    async def ShowTasks(message: Message):
        user = message.from_user.id
        text, IsNextPage, _ = await RenderPages(user_id=user, page=0)
        await message.answer(text, reply_markup= await kb.inline_tasks(next_page=IsNextPage, page=0))

    #edit tasks
    @router.message(F.text == "Изменить задачу")
    async def GetUpdateTask(message: Message, state: FSMContext):
        user = message.from_user.id
        await state.set_state(Action.action)
        await state.update_data(action= "edit")
        text, IsNextPage, tasks = await RenderPages(user_id=user, page=0)
        await message.answer(text, reply_markup= await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=0))

    @router.message(EditTask.task)
    async def UpdateTask(message: Message, state: FSMContext):
        data = await state.get_data()
        taskID = data.get("taskID")
        async with db.AsyncSession() as session:
            stmt = (
                select(db.Task)
                .where(db.Task.id == taskID)
            )
            result = await session.execute(stmt)
            task = result.scalars().first()

            if task:
                task.text = message.text
                await session.commit()

        await state.clear()
        await state.set_state(Action.action)
        await state.update_data(action= "edit")
        text, IsNextPage, tasks = await RenderPages(user_id=message.from_user.id, page=0)
        await message.answer(text, reply_markup=await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=0))

    #delete tasks
    @router.message(F.text == "Удалить задачу")
    async def deleteTask(message: Message, state: FSMContext):
        user = message.from_user.id
        await state.set_state(Action.action)
        await state.update_data(action= "delete")
        text, IsNextPage, tasks = await RenderPages(user_id=user, page=0)
        await message.answer(text, reply_markup= await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=0))

    # change task's status
    @router.message(F.text == "Статус задачи")
    async def GetChangeTaskStatus(message: Message, state: FSMContext):
        user = message.from_user.id
        await state.set_state(Action.action)
        await state.update_data(action= "status")
        text, IsNextPage, tasks = await RenderPages(user_id=user, page=0)
        await message.answer(text, reply_markup= await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=0))

    @router.message(EditStatus.status) #---------------------------------------------------------------------------------
    async def ChangeTaskStatus(message: Message, state: FSMContext):
        data = await state.get_data()
        taskID = data.get("taskID")
        messageID = data.get("messageID")
        await bot.delete_message(chat_id=message.chat.id, message_id=messageID)
        await state.update_data(messageID=None)
        statuses = ["To Do 📝", "In progress ⏳", "Done ✅"]
        if(message.text in statuses):
            async with db.AsyncSession() as session:
                stmt = (
                    select(db.Task)
                    .where(db.Task.id == taskID)
                )
                result = await session.execute(stmt)
                task = result.scalars().first()

                if task:
                    task.status = message.text
                    await session.commit()

        else:
            await message.answer("Такого статуса нет")
        await state.clear()
        await state.set_state(Action.action)
        await state.update_data(action= "status")
        text, IsNextPage, tasks = await RenderPages(user_id=message.from_user.id, page=0)
        await message.answer(text, reply_markup=await kb.inline_tasks(tasks=tasks, next_page=IsNextPage, page=0))

    #Debuging
    @router.message(F.text == "Сообщить об ошибке")
    async def SendDebugMessage(message: Message, state: FSMContext):
        await state.set_state(DebugMessage.text)
        await message.answer("с какой проблемой вы столкнулись? ✏️", reply_markup=kb.cancel)

    @router.message(DebugMessage.text, F.text == "/Отмена")
    async def CancelDebugMessage(message: Message, state: FSMContext):
        await message.answer("Сообщение об ошибке отменено ⚠️❌",
                             reply_markup=kb.mainMenu)
        await state.clear()

    @router.message(DebugMessage.text)
    async def GetDebugMessage(message: Message, state: FSMContext):
        await bot.send_message(IDForDebugMessage, f"Пользователь: {message.from_user.username}\n\nошибка: {message.text}\n")
        await message.answer("ваше сообщение об ошибке успешно отправлено 🎉✅\nспасибо, что помогаете мне стать лучше",
                             reply_markup=kb.mainMenu)
        await state.clear()

    #fallback
    @router.message()
    async def fallback_handler(message: Message):
        await message.answer("Я не понял команду", reply_markup=kb.mainMenu)