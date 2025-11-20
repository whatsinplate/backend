from fastapi import FastAPI
import uvicorn
from routers.auth import router as auth_router
from routers.user_info import router as user_info_router
from database.db_manager import DBManager

app = FastAPI()

app.include_router(auth_router, prefix='/api/auth', tags=['auth'])
app.include_router(user_info_router, prefix='/api/user_info', tags=['user_info'])

@app.get('/ping')
def test():
	return {'pong': 200}

if __name__ == '__main__':
	DBManager()
	uvicorn.run(app, host='0.0.0.0', port=8000)
