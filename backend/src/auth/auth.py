from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from models import User
from db import get_db
from sqlmodel import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SECRET_KEY = "testkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """is password ok"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """get password hash"""
    return pwd_context.hash(password)


def get_user_from_db(userid: str) -> User:
    """get user by id"""
    with get_db() as db:
        user = db.exec(select(User).where(User.id == userid)).first()
    return user


def decode_token(token: str) -> dict:
    """解碼token並返回payload"""
    return jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)


def create_access_token(userid: str) -> str:
    """access token"""
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "userid": str(userid), "type": "access"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(userid: str) -> str:
    """refresh token"""
    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "userid": str(userid), "type": "refresh"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_tokens(user: User) -> dict:
    """create token and reflash token"""
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


def verify_token(token: str) -> str:
    """is JWT token ok"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        userid: str = payload.get("userid")
        if userid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
            )
        return userid
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """獲取當前使用者"""
    userid = verify_token(token)
    user = get_user_from_db(userid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )
    return user


async def is_admin(current_user: User = Depends(get_user)) -> User:
    """is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="you are not admin"
        )
    return current_user
