from fastapi import APIRouter, Request, Depends, HTTPException
import req_models
from database.db_provider import get_db
from database.db_manager import DBManager

router = APIRouter()

@router.get('/get_record')
def get_record(auth_token: str, date: str, db: DBManager = Depends(get_db)):
	uid = db.get_user_id_by_token(auth_token)
	if uid:
		record = db.get_tracker_record(uid, date)
		if record:
			return {'meals': record[0].split('|')}
		else:
			raise HTTPException(status_code=204)
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)

@router.post('/save_meal')
def save_meal(model: req_models.SaveMealRequestModel,
			  db: DBManager = Depends(get_db)):
	uid = db.get_user_id_by_token(model.auth_token)
	if uid:
		status = db.save_meal_to_tracker(uid, model.meal_id)
		if status:
			return {'message': 'The meal was successfully saved.'}
		else:
			raise HTTPException(
				status_code=404, detail={'message': 'No such meal.'}
			)
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)
