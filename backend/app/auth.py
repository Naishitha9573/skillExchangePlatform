from datetime import datetime, timedelta, timezone
import secrets
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db import get_db
from app.models import User

pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(password: str): return pwd_context.hash(password)
def verify_password(password: str, hashed: str | None): return bool(hashed) and pwd_context.verify(password, hashed)

def _secret_key():
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must be configured with at least 32 characters")
    return settings.SECRET_KEY

def create_token(user_id: int):
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub":str(user_id),"exp":exp,"type":"access"}, _secret_key(), algorithm="HS256")

def create_oauth_state():
    expires=datetime.now(timezone.utc)+timedelta(minutes=10)
    return jwt.encode({"nonce":secrets.token_urlsafe(24),"exp":expires,"type":"oauth_state"}, _secret_key(), algorithm="HS256")

def verify_oauth_state(state: str):
    payload=jwt.decode(state, _secret_key(), algorithms=["HS256"])
    if payload.get("type") != "oauth_state" or not payload.get("nonce"):
        raise JWTError("Invalid OAuth state")
    return payload

def current_user(token:str=Depends(oauth2_scheme), db:Session=Depends(get_db)):
    cred_exc=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired token",headers={"WWW-Authenticate":"Bearer"})
    try:
        payload=jwt.decode(token, _secret_key(), algorithms=["HS256"])
        uid=int(payload.get("sub"))
        if payload.get("type") != "access": raise cred_exc
    except (JWTError, TypeError, ValueError, RuntimeError): raise cred_exc
    user=db.get(User,uid)
    if not user: raise cred_exc
    return user
