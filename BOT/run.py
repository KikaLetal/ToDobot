import asyncio
import aiogram
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router, RegisterHandlers
from app.DataBase import initDB


bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await initDB()

    RegisterHandlers(bot)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")

