from fastapi.security import OAuth2PasswordBearer
from fastapi import Request

# Simulated session storage
session_storage = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_session(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token not in session_storage:
        return None
    user = session_storage[session_token]
    return {"email": user["username"], "user": user}