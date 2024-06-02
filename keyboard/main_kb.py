from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Main keyboard
startSearch = KeyboardButton("/StartSearch")
editProfile = KeyboardButton("/EditProfile")
viewMatches = KeyboardButton("/ViewMyMatches")
viewProfile = KeyboardButton("/ViewMyProfile")
viewContacts = KeyboardButton("/ViewMyContacts")
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(startSearch).\
insert(viewMatches).add(viewContacts).add(editProfile).insert(viewProfile)

stopSearch = KeyboardButton("/Menu")
stop_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(stopSearch)



