from pydantic import BaseModel

class AuthRequestModel(BaseModel):
	login: str
	password: str

class RegisterRequestModel(BaseModel):
	login: str
	password: str
	secret_q: str
	secret_q_ans: str

class ResetPasswordRequestModel(BaseModel):
	login: str
	secret_q_ans: str
	new_password: str

class DeleteAccountRequestModel(BaseModel):
	auth_token: str
	password: str
