from datetime import datetime, timedelta, timezone
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

def hash_password(password): return pwd_context.hash(password)
def verify_password(password, hashed): return pwd_context.verify(password, hashed)
def create_token(user_id):
    exp=datetime.now(timezone.utc)+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub":str(user_id),"exp":exp}, settings.SECRET_KEY, algorithm="HS256")
def current_user(token:str=Depends(oauth2_scheme), db:Session=Depends(get_db)):
    cred_exc=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired token",headers={"WWW-Authenticate":"Bearer"})
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        uid=int(payload.get("sub"))
    except (JWTError, TypeError, ValueError): raise cred_exc
    user=db.get(User,uid)
    if not user: raise cred_exc
    return user
