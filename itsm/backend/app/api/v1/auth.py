import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.utils import hash_password, verify_password
from app.db.session import get_db
from app.core.config import settings
from app.controller.user_controller import get_user_data, get_user_hash_pwd
from app.controller.customeruser_controller import get_customeruser_data, get_customeruser_hash_pwd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter()

# ── Pydantic models ──────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    valid_id: Optional[int] = None

class UserInDB(User):
    hashed_password: str

# ── Token helpers ────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token creation failed")

# ── Agent auth ───────────────────────────────────────────────────────────────

def _get_agent(db: Session, login: str):
    try:
        return get_user_data(db, login)
    except Exception as e:
        logger.error(f"Error fetching agent: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user data")

def authenticate_agent(db: Session, login: str, password: str):
    user = _get_agent(db, login)
    if not user:
        return None
    hashed = get_user_hash_pwd(db, login)
    if not hashed or not verify_password(password, hashed):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise credentials_exception

    user = _get_agent(db, login=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.get("valid_id") != 1:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ── Customer auth ────────────────────────────────────────────────────────────

def _get_customer(db: Session, login: str):
    try:
        return get_customeruser_data(db, login)
    except Exception as e:
        logger.error(f"Error fetching customer user: {e}")
        raise HTTPException(status_code=500, detail="Error fetching customer user data")

def authenticate_customer(db: Session, login: str, password: str):
    user = _get_customer(db, login)
    if not user:
        return None
    hashed = get_customeruser_hash_pwd(db, login)
    if not hashed or not verify_password(password, hashed):
        return None
    return user

# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/token", response_model=Token)
async def agent_login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """Agent (staff) login — returns a JWT with user_type='agent'."""
    user = authenticate_agent(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user["login"], "user_type": "agent"},
        expires_delta=expires,
    )
    return {"access_token": token, "token_type": "bearer", "user_type": "agent"}


@router.post("/customer/login", response_model=Token)
async def customer_login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """Customer user login — returns a JWT with user_type='customer'."""
    user = authenticate_customer(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user["login"], "user_type": "customer"},
        expires_delta=expires,
    )
    return {"access_token": token, "token_type": "bearer", "user_type": "customer"}


@router.get("/me/")
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user
