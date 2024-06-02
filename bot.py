from aiogram.utils import executor 


import handlers
from create import dp
from database.sqlite import sql_start


async def on_startup(_):
	print("Bot is up and running")
	sql_start()



executor.start_polling(dp, skip_updates=True, on_startup=on_startup)