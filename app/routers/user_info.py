from fastapi import APIRouter, Request, Depends, HTTPException, Query
import req_models
from database.db_provider import get_db
from database.db_manager import DBManager

router = APIRouter()

@router.get('/get')
def get_user_info(auth_token: str,
				  db: DBManager = Depends(get_db)):
	user_info = db.get_user_info(auth_token)
	if user_info is not None:
		if user_info:
			return {
				'age': user_info[0],
				'gender': user_info[1],
				'height': user_info[2],
				'weight': user_info[3],
				'goal': user_info[4]
			}
		else:
			raise HTTPException(status_code=204)
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)

@router.post('/set')
def set_user_info(model: req_models.SetUserInfoRequestModel,
				  db: DBManager = Depends(get_db)):
	status = db.set_user_info(
		model.auth_token,
		model.age,
		model.gender,
		model.height,
		model.weight,
		model.goal
	)
	if status:
		return {'message': 'User info was successfully updated.'}
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)
