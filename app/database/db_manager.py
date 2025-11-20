import sqlite3
import config
import bcrypt
import uuid
import os
from datetime import datetime

SECONDS_IN_DAY = 86400

class DBManager:
	def __init__(self):
		self.connection = None
		self.cursor = None

		if not os.path.exists(config.DB_PATH):
			self.init_new_db()

	def connect(self):
		self.connection = sqlite3.connect(config.DB_PATH)
		self.cursor = self.connection.cursor()

	def close(self):
		if self.cursor:
			self.cursor.close()
		if self.connection:
			self.connection.close()

	def init_new_db(self):
		self.connect()
		tables = (
			'users(uid, login, pwd_bcrypt, secret_q, secret_q_ans_bcrypt)',
			'tokens(token, uid, expiration_timestamp)',
			'user_info(uid, age, gender, height, weight, goal)',
			'meals(id, name, ingredients, calories, proteins, fats, '
				  'carbohydrates, img_base64, owner_uid)',
			'tracker(uid, date, saved_meals)'
		)

		for table in tables:
			self.cursor.execute(f'CREATE TABLE {table}')

		self.connection.commit()
		self.close()

	def check_credentials(self, login, password):
		query = 'SELECT uid, pwd_bcrypt FROM users WHERE login=?'
		result = self.cursor.execute(query, (login,)).fetchone()
		if result:
			password_hash = result[1]
			if bcrypt.checkpw(password.encode(), password_hash):
				return result[0]
		return None

	def user_exists(self, login):
		query = 'SELECT uid FROM users WHERE login=?'
		result = self.cursor.execute(query, (login,)).fetchone()
		return bool(result)

	def new_user(self, login, password, secret_q, secret_q_answer):
		uid = str(uuid.uuid4())
		password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
		secret_q_ans_hash = bcrypt.hashpw(
			secret_q_answer.encode(), bcrypt.gensalt()
		)
		query = '''INSERT INTO users(
			uid, login, pwd_bcrypt, secret_q, secret_q_ans_bcrypt
			)  VALUES (?, ?, ?, ?, ?)
		'''
		self.cursor.execute(query, (uid, login, password_hash,
									secret_q, secret_q_ans_hash))
		self.connection.commit()

	def unix_time(self):
		return int(datetime.now().timestamp())

	def new_token(self, uid):
		token = str(uuid.uuid4())
		expiration_timestamp = self.unix_time() + SECONDS_IN_DAY
		query = '''INSERT INTO tokens(
			token, uid, expiration_timestamp) VALUES (?, ?, ?)'''
		self.cursor.execute(query, (token, uid, expiration_timestamp))
		self.connection.commit()
		return token

	def get_user_id_by_token(self, token):
		query = 'SELECT * FROM tokens WHERE token=?'
		result = self.cursor.execute(query, (token,)).fetchone()
		if result:
			expiration_timestamp = result[2]
			if self.unix_time() < expiration_timestamp:
				return result[1]
		return None

	def secret_question(self, login):
		query = 'SELECT secret_q FROM users WHERE login=?'
		result = self.cursor.execute(query, (login,)).fetchone()
		return result[0]

	def reset_password(self, login, secret_q_ans, new_password):
		query = 'SELECT secret_q_ans_bcrypt FROM users WHERE login=?'
		secret_q_ans_hash = self.cursor.execute(
									query, (login,)).fetchone()[0]
		if bcrypt.checkpw(secret_q_ans.encode(), secret_q_ans_hash):
			new_pwd_hash = bcrypt.hashpw(new_password.encode(),
										 bcrypt.gensalt())
			query = 'UPDATE users SET pwd_bcrypt=? WHERE login=?'
			self.cursor.execute(query, (new_pwd_hash, login))
			self.connection.commit()
			return True
		return False

	def revoke_tokens(self, auth_token):
		uid = self.get_user_id_by_token(auth_token)
		if uid:
			query = 'UPDATE tokens SET expiration_timestamp=0 WHERE uid=?'
			self.cursor.execute(query, (uid,))
			self.connection.commit()
			return True
		return False

	def rm_user(self, auth_token, password):
		uid = self.get_user_id_by_token(auth_token)
		if uid:
			query = 'SELECT pwd_bcrypt FROM users WHERE uid=?'
			passwd_hash = self.cursor.execute(query, (uid,)).fetchone()[0]
			if bcrypt.checkpw(password.encode(), passwd_hash):
				self.revoke_tokens(auth_token)
				tables = (
					('users', 'uid'),
					('tokens', 'uid'),
					('user_info', 'uid'),
					('meals', 'owner_uid'),
					('tracker', 'uid')
				)
				for table, column in tables:
					self.cursor.execute(
						'DELETE FROM {table} WHERE {column}=?', (uid,)
					)
				self.connection.commit()
				return True
		return False

	def get_user_info(self, auth_token):
		uid = self.get_user_id_by_token(auth_token)
		if uid:
			query = 'SELECT * FROM user_info WHERE uid=?'
			result = self.cursor.execute(query, (uid,)).fetchone()
			if result:
				return result[1:]
			return ()
		return None

	def set_user_info(self, auth_token, age, gender, height, weight, goal):
		uid = self.get_user_id_by_token(auth_token)
		if uid:
			user_info = self.get_user_info(auth_token)
			if user_info:
				query = '''UPDATE user_info SET
					age=?, gender=?, height=?, weight=?,
					goal=? WHERE uid=?'''
				self.cursor.execute(query, (
					age, gender, height, weight, goal, uid
				))
			else:
				query = '''INSERT INTO user_info(
					uid, age, gender, height, weight, goal)
					VALUES (?, ?, ?, ?, ?, ?)'''
				self.cursor.execute(query, (
					uid, age, gender, height, weight, goal
				))
			self.connection.commit()
			return True
		return False
