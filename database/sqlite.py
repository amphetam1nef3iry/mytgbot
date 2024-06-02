import sqlite3 as sq 


# create all sql tables
def sql_start():
	global base, cur
	base = sq.connect("mybot_database.db")
	cur = base.cursor()

	if base:
		print("Successfully connected to the database")

	# users database
	cur.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT, avatar TEXT,\
	 age TEXT, about TEXT, reason TEXT, username TEXT)")
	base.commit()

	# matches database
	cur.execute("CREATE TABLE IF NOT EXISTS matches(from_user REFERENCES\
	 users(id), to_user REFERENCES users(id), positive BOOL, CONSTRAINT unq UNIQUE (from_user, to_user))")
	base.commit()


async def sql_is_registered(id):
	res = cur.execute("SELECT name FROM users WHERE id = ?", (id,)).fetchone()
	if res:
		return True
	else:
		return False


# Register user
async def sql_register_user(data):
	# data has keys name, id, avatar, age, about, reason
	cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", (data["id"], \
		data["name"], data["avatar"], data["age"], data["about"], data["reason"], data["username"]))
	base.commit()


# Edit user's profile
async def edit_user_profile(data):
	# data has keys name, id, avatar, age, about, reason
	cur.execute("UPDATE users SET name=$1, avatar=$2, age=$3, about=$4,\
	 reason=$5 WHERE id=$6", (data["name"], data["avatar"], \
	 data["age"], data["about"], data["reason"], data["id"]))
	base.commit()


async def fetch_potential_match(id):
	match = cur.execute("SELECT * FROM users WHERE NOT id = $1 AND id NOT IN \
		(SELECT to_user FROM matches WHERE from_user=$1)\
		 AND id NOT IN (SELECT from_user FROM matches WHERE to_user=$1) LIMIT 1", (str(id), )).fetchone()
	return match


# Like a user
async def sql_like_user(from_user, to_user):
	cur.execute("INSERT INTO matches VALUES (?, ?, True)", (from_user, to_user))
	base.commit()

# Pass a user
async def sql_pass_user(from_user, to_user):
	cur.execute("INSERT INTO matches VALUES (?, ?, False)", (from_user, to_user))
	base.commit()


# Fetch matches ### FIND A WAY TO OPTIMIZE
async def fetch_match(id):
	profile = cur.execute("SELECT * FROM users WHERE id IN (SELECT from_user FROM \
		matches WHERE positive=True and to_user=$1) AND id NOT IN (SELECT to_user \
		FROM matches WHERE from_user=$1) LIMIT 1;", (str(id), ))
	return profile.fetchone()


# View user's profile
async def view_profile(id):
	return cur.execute("SELECT * FROM users WHERE id=$1", (str(id), )).fetchone()


# Fetch contacts
async def fetch_contacts(id):
	return cur.execute("SELECT * FROM users WHERE \
		id IN (SELECT from_user FROM matches WHERE \
		to_user=$1 AND positive=True AND from_user IN\
		 (SELECT to_user FROM matches WHERE from_user=$1\
		  AND positive=True))", (str(id), )).fetchall()








