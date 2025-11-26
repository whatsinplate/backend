from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
import req_models
from database.db_provider import get_db
from database.db_manager import DBManager

import config
from google import genai
from google.genai import types

import base64
import json

PNG_SIGNATURE = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
JPEG_SIGNATURE = b'\xff\xd8\xff'
WEBP_SIGNATURE = b'\x57\x45\x42\x50'

router = APIRouter()
client = genai.Client(api_key=config.GEMINI_API_KEY)

script_dir = '/'.join(__file__.split('/')[:-1])
scan_prompt_path = f'{script_dir}/../static/scan_prompt.txt'
with open(scan_prompt_path, 'r') as file:
	scan_prompt = file.read()

recommendation_prompt_path = f'{script_dir}/../static/recommendation_prompt.txt'
with open(recommendation_prompt_path, 'r') as file:
	recommendation_prompt = file.read()

@router.post('/scan')
async def scan(model: req_models.ScanRequestModel,
			   db: DBManager = Depends(get_db)):
	uid = await run_in_threadpool(
		db.get_user_id_by_token, model.auth_token
	)
	if uid:
		image_bytes = base64.b64decode(model.img_base64)
		if image_bytes.startswith(PNG_SIGNATURE):
			image_mime_type = 'image/png'
		elif image_bytes.startswith(JPEG_SIGNATURE):
			image_mime_type = 'image/jpeg'
		elif image_bytes[8:12] == WEBP_SIGNATURE:
			image_mime_type = 'image/webp'
		else:
			raise HTTPException(
				status_code=400,
				detail={
					'message': 'File format is not JPEG, PNG, or WEBP.'
				}
			)

		response = await client.aio.models.generate_content(
			model=config.AI_MODEL,
			contents=[
				types.Part.from_bytes(data=image_bytes,
									  mime_type=image_mime_type),
				scan_prompt
			]
		)
		try:
			parsed = json.loads(response.text)
			if parsed['status'] == 'ok':
				meal_id = await run_in_threadpool(
					db.add_meal, uid, parsed, model.img_base64
				)
				return {'meal_id': meal_id}
			else:
				raise HTTPException(
					status_code=422,
					detail={
						'message': 'The image does not seem to contain food.'
					}
				)
		except json.decoder.JSONDecodeError:
			raise HTTPException(
				status_code=500,
				detail={
					'message': 'AI response is not a valid JSON. Try again.'
				}
			)

	else:
		raise HTTPException(
			status_code=401, detail={'message': 'Token is invalid.'}
		)

@router.get('/recommendation')
async def get_recommendation(auth_token: str,
							 date: str,
							 db: DBManager = Depends(get_db)):
	uid = await run_in_threadpool(
		db.get_user_id_by_token, auth_token
    )
	if uid:
		tracker_record = await run_in_threadpool(
			db.get_tracker_record, uid, date
		)
		if tracker_record:
			meals = []
			for meal_id in tracker_record.split('|'):
				meal = await run_in_threadpool(db.get_meal, meal_id)
				meals.append(meal[0])
			user_info_entry = await run_in_threadpool(db.get_user_info, auth_token)
			user_info = {
				'age': user_info_entry[0],
				'gender': user_info_entry[1],
				'height': f'{user_info_entry[2]} cm',
				'weight': f'{user_info_entry[3]} kg',
				'goal': user_info_entry[4]
			}
			response = await client.aio.models.generate_content(
            	model=config.AI_MODEL,
            	contents=[
                	recommendation_prompt + str(user_info) + '\n\n' + str(meals)
				]
        	)
			return {'recommendation': response.text}

		else:
			raise HTTPException(
				status_code=204,
				detail={'message': 'No meals are saved this day.'}
			)
	else:
		raise HTTPException(
			status_code=401,
			detail={'message': 'Token is invalid.'}
		)

