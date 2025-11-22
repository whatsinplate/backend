from fastapi import APIRouter, Request, Depends, HTTPException
from database.db_provider import get_db
from database.db_manager import DBManager

router = APIRouter()

@router.get('/info')
def info(auth_token: str,
		 meal_id: str,
		 db: DBManager = Depends(get_db)):
	uid = db.get_user_id_by_token(auth_token)
	if uid:
		meal = db.get_meal(meal_id)
		if meal:
			if meal[-2] == uid:
				return {
					'meal_name': meal[0],
					'ingredients': meal[1].split('|'),
					'calories': meal[2],
					'proteins': meal[3],
					'fats': meal[4],
					'carbohydrates': meal[5],
					'timestamp': meal[-1]
				}
			else:
				raise HTTPException(
					status_code=403, detail={
						'message': 'This meal is registered by another user.'
					}
				)
		else:
			raise HTTPException(
				status_code=404, detail={'message': 'No such meal.'}
			)
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)

@router.get('/photo')
def photo(auth_token: str,
		  meal_id: str,
		  db: DBManager = Depends(get_db)):
	uid = db.get_user_id_by_token(auth_token)
	if uid:
		result = db.meal_photo(meal_id)
		if result:
			if result[0] == uid:
				return {'img_base64': result[1]}
			else:
				raise HTTPException(
					status_code=403, detail={
						'message': 'This meal is registered by another user.'
					}
				)
		else:
			raise HTTPException(
				status_code=404, detail={'message': 'No such meal.'}
			)
	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)
