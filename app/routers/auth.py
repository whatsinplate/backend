from fastapi import APIRouter, Request, Depends, HTTPException, Query
import req_models
from database.db_provider import get_db
from database.db_manager import DBManager

router = APIRouter()

@router.post('/login')
def login(model: req_models.AuthRequestModel,
		  db: DBManager = Depends(get_db)):
	uid = db.check_credentials(model.login, model.password)
	if uid:
		return {'token': db.new_token(uid)}
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Credentials were wrong.'}
		)

@router.post('/register')
def register(model: req_models.RegisterRequestModel,
			 db: DBManager = Depends(get_db)):
	if not db.user_exists(model.login):
		db.new_user(
			model.login, model.password, model.secret_q, model.secret_q_ans
		)
		return {'message': 'User was successfully created.'}
	else:
		raise HTTPException(
			status_code=409, detail={'message': 'User already exists.'}
		)

@router.get('/iforgot')
def iforgot(login: str, db: DBManager = Depends(get_db)):
	if db.user_exists(login):
		secret_question = db.secret_question(login)
		return {'secret_q': secret_question}
	else:
		raise HTTPException(
			status_code=404, detail={'message': 'User does not exist.'}
		)

@router.post('/reset_password')
def reset_password(model: req_models.ResetPasswordRequestModel,
				   db: DBManager = Depends(get_db)):
	if db.user_exists(model.login):
		status = db.reset_password(
			model.login, model.secret_q_ans, model.new_password
		)
		if status:
			return {'message': 'Password has been reset.'}
		else:
			raise HTTPException(
				status_code=401,
				detail={'message': 'Secret question answer was wrong.'}
			)
	else:
		raise HTTPException(
			status_code=404, detail={'message': 'User does not exist.'}
		)

@router.get('/revoke_tokens')
def revoke_auth_tokens(auth_token: str, db: DBManager = Depends(get_db)):
	status = db.revoke_tokens(auth_token)
	if status:
		return {'message': 'All tokens have been revoked.'}
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)

@router.post('/delete_account')
def delete_account(model: req_models.DeleteAccountRequestModel,	
				   db: DBManager = Depends(get_db)):
	status = db.rm_user(model.auth_token, model.password)
	if status:
		return {'message': 'Account has been deleted successfully.'}
	else:
		raise HTTPException(
			status_code=401,
			detail={'message': 'Token or password was wrong.'}
		)
