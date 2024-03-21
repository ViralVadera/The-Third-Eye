from fastapi.security import OAuth2PasswordBearer
from fastapi import Request
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Simulated session storage
session_storage = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_session(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token not in session_storage:
        return None
    user = session_storage[session_token]
    return {"email": user["username"], "user": user, "user_type": user["user_type"]} 

def encrypt_password(new_password):
    hashed_password = bcrypt_context.hash(new_password)
    return hashed_password