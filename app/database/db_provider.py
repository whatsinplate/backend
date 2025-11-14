from database.db_manager import DBManager
from fastapi import Depends

def get_db():
	db = DBManager()
	db.connect()
	try:
		yield db
	finally:
		db.close()