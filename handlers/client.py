import sqlite3
from aiogram import types 
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from create import dp, bot
from database.sqlite import sql_is_registered, sql_register_user
from database.sqlite import fetch_potential_match, fetch_match
from database.sqlite import sql_like_user, sql_pass_user
from database.sqlite import edit_user_profile
from database.sqlite import view_profile
from database.sqlite import fetch_contacts
from keyboard.registration_kb import register_kb
from keyboard.main_kb import main_kb, stop_kb
from keyboard.edit_profile import edit_kb

class Registration(StatesGroup):
	name = State()
	avatar = State()
	age = State()
	about = State()
	reason = State()


class EditProfile(StatesGroup):
	name = State()
	avatar = State()
	age = State()
	about = State()
	reason = State()


@dp.message_handler(commands="start")
async def on_start_handler(message : types.Message):
	if await sql_is_registered(message.from_user.id):
		# User is already registered
		await message.answer("We are glad to see you here again!", reply_markup=main_kb)
	else:
		# User is new
		await bot.send_message(message.from_user.id, "Welcome to mybot", reply_markup=register_kb)


# Registration includes name, avatar, age, about, reason
@dp.message_handler(commands="register")
async def register_handler(message : types.Message):
	if await sql_is_registered(message.from_user.id):
		# already registered
		await message.answer("You are already registered!")
	else:
		# new user
		await Registration.name.set()
		await message.answer("Please type in your name", reply_markup=ReplyKeyboardRemove())


@dp.message_handler(state=Registration.name)
async def registration_set_name(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["name"] = message.text
		data["id"] = message.from_user.id
	await Registration.next()
	await message.answer("Please load your avatar")


@dp.message_handler(content_types=["photo"], state=Registration.avatar)
async def registration_set_avatar(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["avatar"] = message.photo[0].file_id
	await Registration.next()
	await message.answer("Please type in your age")


@dp.message_handler(state=Registration.age)
async def registration_set_age(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["age"] = message.text
	await Registration.next()
	await message.answer("Please tell us some interesting facts about yourself")


@dp.message_handler(state=Registration.about)
async def registration_set_about(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["about"] = message.text
	await Registration.next()
	await message.answer("Please tell us your reason for using mybot")


@dp.message_handler(state=Registration.reason)
async def registration_set_reason(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["reason"] = message.text
		data["username"] = message.from_user.username
		await sql_register_user(data)
	await state.finish()
	await message.answer("Your registration is complete. You can start searching for people now", \
		reply_markup=main_kb)


# Searching matches
@dp.message_handler(commands="StartSearch")
async def start_matches_search(message : types.Message):
	await message.answer("Checking for potential matches...", reply_markup=stop_kb)

	try:
		# match: id, name, photo, age, about, reason
		match = await fetch_potential_match(message.from_user.id)
	
		if not match:
			await message.answer("Sorry, there is no one left to match")
			return


		# Constructing the inline keyboard
		markup = InlineKeyboardMarkup(resize_keyboard=True)
		markup.add(InlineKeyboardButton(text="Like", callback_data=f"Like;{message.from_user.id};{match[0]};1"))
		markup.insert(InlineKeyboardButton(text="Pass", callback_data=f"Like;{message.from_user.id};{match[0]};0"))
		
		text = "<i>Name: </i><b>{}</b>\nAge: {}\n<i>About: </i>{}\n<i>Reason for using Davinchik: </i>{}".format(match[1], match[3], match[4], match[5])
		await bot.send_photo(message.from_user.id, match[2], text, reply_markup=markup, parse_mode="HTML")
	except DatabaseError as e:
		if await sql_is_registered(message.from_user.id):
			await message.answer("Error. Please try again")
		else:
			await message.answer("Please register first", reply_markup=register_kb)

# Callback query handlers
@dp.callback_query_handler(Text(startswith="Like;"))
async def like_callback(callback : types.CallbackQuery):
	from_user, user_id, action = callback.data.split(";")[1:]
	error = None
	if action == 0:
		try:
			await sql_pass_user(from_user, user_id)
		except DatabaseError as e:
			await callback.answer("You have already reacted to this profile", show_alert=True)
			error = e
	else:
		try: 
			await sql_like_user(from_user, user_id)
		except sqlite3.DatabaseError as e:
			await callback.answer("You have already reacted to this profile", show_alert=True)
			error = e

	if error == None:
		message = None
		match = await fetch_potential_match(from_user)
		if not match:
			await callback.message.answer("No one left to match")
			return
		# Constructing the inline keyboard
		markup = InlineKeyboardMarkup(resize_keyboard=True)
		markup.add(InlineKeyboardButton(text="Like", callback_data=f"Like;{from_user};{match[0]};1"))
		markup.insert(InlineKeyboardButton(text="Pass", callback_data=f"Like;{from_user};{match[0]};0"))
		
		text = "<i>Name: </i><b>{}</b>\nAge: {}\n<i>About: </i>{}\n<i>Reason for using mybot: </i>{}".format(match[1], match[3], match[4], match[5])
		await bot.send_photo(from_user, match[2], text, reply_markup=markup, parse_mode="HTML")
	await callback.answer()
		


# Stopping the search
@dp.message_handler(commands="Menu")
async def stop_search(message : types.Message):
	try:
		await message.answer("Stopped the search.", reply_markup=main_kb)
	except DatabaseError as e:
		if await sql_is_registered(message.from_user.id):
			await message.answer("Error. Please try again")
		else:
			await message.answer("Please register first", reply_markup=register_kb)


# Editing profile
@dp.message_handler(commands="EditProfile")
async def edit_profile_handler(message : types.Message):
	if not await sql_is_registered(message.from_user.id):
		# not registered
		await message.answer("You are not registered!")
	else:
		# new user
		await EditProfile.name.set()
		await message.answer("Please type in your new name", reply_markup=edit_kb)

# Cancel editing profile
@dp.message_handler(commands="cancel", state="*")
async def cancel_editing(message : types.Message, state : FSMContext):
	try:
		await message.answer("Cancelled editing profile", reply_markup=main_kb)
		await state.finish()
	except DatabaseError as e:
		if await sql_is_registered(message.from_user.id):
			await message.answer("Error. Please try again")
		else:
			await message.answer("Please register first", reply_markup=register_kb)

@dp.message_handler(state=EditProfile.name)
async def edit_set_name(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["name"] = message.text
		data["id"] = message.from_user.id
	await EditProfile.next()
	await message.answer("Please load your new avatar")


@dp.message_handler(content_types=["photo"], state=EditProfile.avatar)
async def edit_set_avatar(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["avatar"] = message.photo[0].file_id
	await EditProfile.next()
	await message.answer("Please type in your new age")


@dp.message_handler(state=EditProfile.age)
async def edit_set_age(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["age"] = message.text
	await EditProfile.next()
	await message.answer("Please tell us some interesting facts about yourself")


@dp.message_handler(state=EditProfile.about)
async def edit_set_about(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["about"] = message.text
	await EditProfile.next()
	await message.answer("Please tell us your reason for using mybot")


@dp.message_handler(state=EditProfile.reason)
async def edit_set_reason(message : types.Message, state : FSMContext):
	async with state.proxy() as data:
		data["reason"] = message.text
		await edit_user_profile(data)
	await state.finish()
	await message.answer("Your data has been successfully changed. You can start searching for people now.", \
		reply_markup=main_kb)



# Viewing profile
@dp.message_handler(commands="ViewMyProfile")
async def view_profile_handler(message : types.Message):
	try:
		p = await view_profile(message.from_user.id)
		await message.answer("Loading your profile.")
		text = "<i>Name: </i><b>{}</b>\nAge: {}\n<i>About: </i>{}\n<i>Reason for using mybot: </i>{}".format(p[1], p[3], p[4], p[5])
		await bot.send_photo(message.from_user.id, p[2], text, parse_mode="HTML")
	except DatabaseError as e:
		if await sql_is_registered(message.from_user.id):
			await message.answer("Error. Please try again")
		else:
			await message.answer("Please register first", reply_markup=register_kb)



# View matches
@dp.message_handler(commands="ViewMyMatches")
async def view_my_matches_handler(message : types.Message):
	try:
		await message.answer("Checking matches...")
		p = await fetch_match(message.from_user.id)
		if not p:
			await message.answer("No new matches...")
			return

		# Constructing the inline keyboard
		from_user = message.from_user.id
		markup = InlineKeyboardMarkup(resize_keyboard=True)
		markup.add(InlineKeyboardButton(text="Like", callback_data=f"LikeMatch;{from_user};{p[0]};1"))
		markup.insert(InlineKeyboardButton(text="Pass", callback_data=f"LikeMatch;{from_user};{p[0]};0"))

		text = "<i>Name: </i><b>{}</b>\nAge: {}\n<i>About: </i>{}\n<i>Reason for using mybot: </i>{}".format(p[1], p[3], p[4], p[5])
		await bot.send_photo(from_user, p[2], text, reply_markup=markup, parse_mode="HTML")
	except DatabaseError as e:
		if await sql_is_registered(message.from_user.id):
			await message.answer("Error. Please try again")
		else:
			await message.answer("Please register first", reply_markup=register_kb)



# Callback query handler for liking a matched user
@dp.callback_query_handler(Text(startswith="LikeMatch;"))
async def likematch_callback(callback : types.CallbackQuery):
	from_user, user_id, action = callback.data.split(";")[1:]
	error = None
	if int(action) == 0:
		try:
			await sql_pass_user(from_user, user_id)
		except DatabaseError as e:
			error = e
	else:
		try: 
			await sql_like_user(from_user, user_id)
		except sqlite3.DatabaseError as e:
			error = e

	if error==None:
		if int(action)=="1":
			await bot.send_message(from_user, "User has been added to your contacts")
		else:
			await bot.send_message(from_user, "User has been passed")

		p = await fetch_match(from_user)
		if not p:
			await callback.message.answer("No matches left")
			return
	
		# Constructing the inline keyboard
		markup = InlineKeyboardMarkup(resize_keyboard=True)
		markup.add(InlineKeyboardButton(text="Like", callback_data=f"LikeMatch;{from_user};{p[0]};1"))
		markup.insert(InlineKeyboardButton(text="Pass", callback_data=f"LikeMatch;{from_user};{p[0]};0"))

		text = "<i>Name: </i><b>{}</b>\nAge: {}\n<i>About: </i>{}\n<i>Reason for using mybot: </i>{}".format(p[1], p[3], p[4], p[5])
		await bot.send_photo(from_user, p[2], text, reply_markup=markup, parse_mode="HTML")
	await callback.answer()



@dp.message_handler(commands="ViewMyContacts")
async def view_contacts_handler(message : types.Message):
	try:
		contacts = await fetch_contacts(message.from_user.id)
		for c in contacts:
			text = "<i>Name: </i><b>{}</b>\nAge: {}\n<i>About: </i>{}\n<i>Reason for using mybot: </i>{}\n<i>Telegram nickname: </i>@{}".format(c[1], c[3], c[4], c[5], c[6])
			await bot.send_photo(message.from_user.id, c[2], text, parse_mode="HTML")
	except DatabaseError as e:
		if await sql_is_registered(message.from_user.id):
			await message.answer("Error. Please try again")
		else:
			await message.answer("Please register first", reply_markup=register_kb)











