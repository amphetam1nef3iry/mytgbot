from aiogram import Bot
from aiogram.dispatcher import Dispatcher 
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import os

token = os.getenv("TOKEN")

storage = MemoryStorage()

bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)




