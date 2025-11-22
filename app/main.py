from fastapi import FastAPI
import uvicorn
from routers.auth import router as auth_router
from routers.user_info import router as user_info_router
from routers.ai import router as ai_router
from routers.meal import router as meal_router
from routers.tracker import router as tracker_router
from database.db_manager import DBManager

app = FastAPI()

app.include_router(auth_router, prefix='/api/auth', tags=['auth'])
app.include_router(user_info_router, prefix='/api/user_info', tags=['user_info'])
app.include_router(ai_router, prefix='/api/ai', tags=['ai'])
app.include_router(meal_router, prefix='/api/meal', tags=['meal'])
app.include_router(tracker_router, prefix='/api/tracker', tags=['tracker'])

@app.get('/ping')
def ping():
	return {'ping': 'pong'}

if __name__ == '__main__':
	DBManager()
	uvicorn.run(app, host='0.0.0.0', port=8000)
