from aiogram.types import ReplyKeyboardMarkup, KeyboardButton 


cancel = KeyboardButton("/cancel")

edit_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(cancel)
