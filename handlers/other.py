from aiogram import types 


from create import dp


# no such command handler
@dp.message_handler()
async def no_such_command(message : types.Message):
	await message.answer("Sorry, no such command")