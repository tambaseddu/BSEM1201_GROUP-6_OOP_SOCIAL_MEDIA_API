import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt  
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import models, database, schemas 
from email_service import send_verification_email 

SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SUPER_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

router = APIRouter(
    prefix="/auth",
    tags=["Modern Authentication Portal"]
)

# --- Token & Hash Helpers ---
def get_password_hash(password: str) -> str: return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool: return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- 🚀 NEW ROUTE: PROCESS THE 6-DIGIT CODE SUBMISSION ---
@router.post("/verify-code")
def verify_code(email: str, code: str, db: Session = Depends(database.get_db)):
    """
    Validates the 6-digit user verification code against the database row.
    """
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account user profile not found.")
        
    if user.is_verified:
        return {"status": "success", "message": "Account already active. Proceed to login."}
        
    # Check if code matches and has not expired yet
    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid 6-digit confirmation pin.")
        
    # Standardize timezone comparison securely
    if datetime.now() > user.verification_expires_at:
        raise HTTPException(status_code=400, detail="This code has expired. Please request a new one.")
        
    # 🔓 Activate account!
    user.is_verified = True
    user.verification_code = None  # Clear the code token after successful activation
    user.verification_expires_at = None
    db.commit()
    
    return {"status": "success", "message": "Identity confirmed successfully! Your account is active."}

# --- 🛣️ Modified Registration Endpoint ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(
        (models.User.email == user_in.email) | (models.User.username == user_in.username)
    ).first()
    
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered.")
        
    # Generate random 6-digit numeric string sequence secure code
    otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
    expiration_window = datetime.now() + timedelta(minutes=15)

    hashed_pwd = get_password_hash(user_in.password)
    new_user = models.User(
        username=user_in.username, 
        email=user_in.email, 
        hashed_password=hashed_pwd,
        is_verified=False,
        verification_code=otp_code,               # 💾 Save to db columns
        verification_expires_at=expiration_window
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Fire background task processing
    background_tasks.add_task(send_verification_email, new_user.email, otp_code)
    
    return {
        "status": "pending",
        "email": new_user.email,
        "message": "Account created. A 6-digit security code has been transmitted to your inbox."
    }