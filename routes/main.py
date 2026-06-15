from fastapi import FastAPI, Depends, Request, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import uuid
import secrets

load_dotenv()

# --- 📁 PATHS & DIRECTORY MANAGEMENT ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Point directly to your root data media directory safely
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FRONTEND_STATIC = os.path.join(BASE_DIR, "frontend", "static")

import models, schemas, database
from database import engine, get_db
from email_service import send_verification_email 

# Create DB tables securely
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Modern Social Media API", 
    version="1.0.0", 
    description="A feature-rich social media backend API built with FastAPI, SQLAlchemy, and JWT authentication. Developed by BSEM1201 GROUP 6",
    docs_url=None, 
    redoc_url=None
)

# 📂 Mount static and uploaded files asset tracking directories
app.mount("/static", StaticFiles(directory=FRONTEND_STATIC), name="static") 
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 🖥️ Connect the HTML template rendering engine
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "frontend", "templates"))

# --- 🔐 INTERNAL AUTHENTICATION CORE CONFIGURATION ---
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SUPER_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_password_hash(password: str) -> str: 
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool: 
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") 
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except JWTError:  
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
        
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email verification required.")
        
    return user

# Custom CSS injected directly into the interactive Swagger UI page context
custom_css = """
:root {
    --primary-color: #dbb583;
    --accent-color: #10b981;
    --bg-dark: #1e293b;
    --bg-card: #0f172a;
    --text-main: #ffffff;
    --text-muted: #94a3b8;
    --border-slate: #334155;
}
body, .swagger-ui {
    background-color: var(--bg-dark) !important;
    color: var(--text-main) !important;
    font-family: 'Tahoma', sans-serif !important;
}
.swagger-ui .topbar { 
    background-color: #020617 !important;
    border-bottom: 2px solid var(--primary-color);
    padding: 12px 0;
}
.swagger-ui .info .title {
    color: var(--primary-color) !important;
    font-family: 'Tahoma', sans-serif !important;
    font-weight: 700 !important;
    text-align: center !important;
}
.swagger-ui .opblock-tag {
    color: #ffffff !important;
    font-weight: 600 !important;
}
.swagger-ui .opblock {
    border-radius: 12px !important;
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-slate) !important;
    margin-bottom: 14px !important;
}
.swagger-ui .opblock-body {
    background-color: #0f172a !important;
}
.swagger-ui input[type=text], .swagger-ui textarea, .swagger-ui select {
    background-color: #1e293b !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border-slate) !important;
}
.swagger-ui .btn.authorize {
    background-color: var(--accent-color) !important;
    color: white !important;
}
.swagger-ui .scheme-container {
    background-color: var(--bg-card) !important;
}
"""

# --- 🌐 WEB VIEW ROUTERS (Serving Visual UI HTML Website Pages) ---

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_login_portal(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard_portal(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/verify", response_class=HTMLResponse, include_in_schema=False)
async def serve_otp_verification_page(request: Request, email: Optional[str] = ""):
    return templates.TemplateResponse(request=request, name="verify.html", context={"email": email})

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Interactive Console",
        oauth2_redirect_url=getattr(app, "oauth2_redirect_url", None),
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    )
    html_content = response.body.decode("utf-8")
    custom_style_tag = f"<style>{custom_css}</style>"
    modified_html = html_content.replace("</head>", f"{custom_style_tag}</head>")
    return HTMLResponse(content=modified_html, status_code=200)


# --- 🔐 MODERN AUTHENTICATION PORTAL ENDPOINTS ---

@app.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["Modern Authentication Portal"])
def register_user(user_in: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        (models.User.email == user_in.email) | (models.User.username == user_in.username)
    ).first()
    
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered.")
        
    otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
    expiration_window = datetime.now() + timedelta(minutes=15)

    hashed_pwd = get_password_hash(user_in.password)
    new_user = models.User(
        username=user_in.username, 
        email=user_in.email, 
        hashed_password=hashed_pwd,
        is_verified=False,
        verification_code=otp_code,
        verification_expires_at=expiration_window
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    background_tasks.add_task(send_verification_email, new_user.email, otp_code)
    
    return {
        "status": "pending",
        "email": new_user.email,
        "message": "Account created. A 6-digit security code has been transmitted to your inbox."
    }

@app.post("/auth/verify-code", tags=["Modern Authentication Portal"])
def verify_code(email: str, code: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account user profile not found.")
        
    if user.is_verified:
        return {"status": "success", "message": "Account already active. Proceed to login."}
        
    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid 6-digit confirmation pin.")
        
    if datetime.now() > user.verification_expires_at:
        raise HTTPException(status_code=400, detail="This code has expired. Please request a new one.")
        
    user.is_verified = True
    user.verification_code = None  
    user.verification_expires_at = None
    db.commit()
    
    return {"status": "success", "message": "Identity confirmed successfully! Your account is active."}

@app.post("/auth/token", response_model=schemas.Token, tags=["Modern Authentication Portal"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account unverified. Please confirm your identity using the 6-digit OTP code sent to your email."
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# --- 👥 USER MANAGEMENT ROUTING WITH ROLE PROTECTION ---

@app.put("/users/{target_user_id}", response_model=schemas.UserResponse, tags=["Users Profile Management"])
def update_user_profile(target_user_id: int, profile_updates: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != target_user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. You can only edit your own account record unless authorized as Admin.")
        
    user_record = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User target not found")
        
    for key, value in profile_updates.model_dump(exclude_unset=True).items():
        if key == "is_admin" and not current_user.is_admin:
            continue 
        setattr(user_record, key, value)
        
    db.commit()
    db.refresh(user_record)
    return user_record


# --- 📰 POST FEED ENGINE ---

@app.post("/posts", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED, tags=["Feed Engine"])
async def create_new_post(
    content: str = Form(...), 
    file: Optional[UploadFile] = File(None), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    media_url_path = None

    if file and file.filename:
        extension = os.path.splitext(file.filename)[1]
        safe_filename = f"post_{current_user.id}_{uuid.uuid4().hex}{extension}"
        file_storage_location = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_storage_location, "wb") as buffer:
            content_bytes = await file.read()
            buffer.write(content_bytes)
            
        media_url_path = f"/uploads/{safe_filename}"

    new_post = models.Post(content=content, media_url=media_url_path, user_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.get("/posts", response_model=List[schemas.PostResponse], tags=["Feed Engine"])
def get_social_feed(limit: int = 20, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Post).order_by(models.Post.created_at.desc()).limit(limit).all()

@app.get("/posts/detailed-feed", tags=["Feed Engine"])
def get_detailed_social_feed(limit: int = 20, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).limit(limit).all()
    
    feed_data = []
    for post in posts:
        post_comments = []
        for comment in post.comments:
            post_comments.append({
                "comment_id": comment.id,
                "content": comment.content,
                "commenter_username": comment.user.username 
            })
            
        feed_data.append({
            "post_id": post.id,
            "content": post.content,
            "media_url": post.media_url,
            "created_at": post.created_at,
            "likes_count": len(post.liked_by),                    
            "author": {
                "id": post.user.id,
                "username": post.user.username,
                "followers_count": len(post.user.followers),
                "following_count": len(post.user.following),
                "profile_pic_url": getattr(post.user, "profile_pic_url", "/static/defaults/default-avatar.png")   
            },
            "comments": post_comments                                  
        })
        
    return feed_data

@app.post("/users/upload-profile-pic", tags=["Users Profile Management"])
async def upload_profile_picture(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File format must be an image.")
        
    extension = os.path.splitext(file.filename)[1]
    unique_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:6]}{extension}"
    
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    current_user.profile_pic_url = f"/uploads/{unique_filename}"
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile picture updated successfully", "url": current_user.profile_pic_url}

@app.put("/posts/{post_id}", response_model=schemas.PostResponse, tags=["Posts Management"])
def update_post(post_id: int, post_update: schemas.PostUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    post_record = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The requested post could not be found.")
        
    if post_record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. You can only edit your own posts.")
        
    post_record.content = post_update.content
    if hasattr(post_update, 'media_url') and post_update.media_url is not None:
        post_record.media_url = post_update.media_url
        
    db.commit()
    db.refresh(post_record)
    return post_record

@app.delete("/posts/{post_id}", status_code=status.HTTP_200_OK, tags=["Posts Management"])
def delete_post(post_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    post_record = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The requested post could not be found.")
        
    if post_record.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. You are not authorized to delete this post.")
        
    db.delete(post_record)
    db.commit()
    return {"status": "success", "message": f"Post with ID {post_id} has been permanently deleted."}


# --- 💬 COMMENTS ENGINE ---

@app.post("/posts/{post_id}/comments", response_model=schemas.CommentResponse, tags=["Comments Management"])
def add_comment_to_post(post_id: int, comment_in: schemas.CommentCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Target post does not exist.")
    
    new_comment = models.Comment(content=comment_in.content, user_id=current_user.id, post_id=post_id)
    db.add(new_comment)
    
    if post.user_id != current_user.id:
        notification = models.Notification(content=f"User '{current_user.username}' commented on your post!", user_id=post.user_id)
        db.add(notification)
        
    db.commit()
    db.refresh(new_comment)
    return new_comment

@app.delete("/comments/{comment_id}", status_code=status.HTTP_200_OK, tags=["Comments Management"])
def delete_comment(comment_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
        
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        
    db.delete(comment)
    db.commit()
    return {"status": "success", "message": f"Comment with ID {comment_id} has been permanently deleted."}

@app.put("/comments/{comment_id}", tags=["Comments Management"])
def update_comment(
    comment_id: int, 
    comment_in: schemas.CommentCreate,  # Uses your comment validation schema
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Updates an existing comment. Only the original author is allowed to edit it.
    """
    # 1. Fetch the comment from the database
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
        
    # 2. Security Check: Ensure the logged-in user owns this comment
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only edit your own comments.")
        
    # 3. Apply changes and commit to database
    comment.content = comment_in.content
    db.commit()
    db.refresh(comment)
    
    return {"status": "success", "message": "Comment updated successfully.", "comment_id": comment.id}


# --- 👍 LIKES INTERACTIONS ---

@app.post("/posts/{post_id}/like", tags=["Interactions Engine"])
def like_post(post_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
        
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
        db.commit()
        return {"status": "success", "message": "Post unliked", "total_likes": len(post.liked_by)}
        
    post.liked_by.append(current_user)
    if post.user_id != current_user.id:
        notification = models.Notification(content=f"User '{current_user.username}' liked your post!", user_id=post.user_id)
        db.add(notification)
        
    db.commit()
    return {"status": "success", "message": "Post liked", "total_likes": len(post.liked_by)}


# --- 👥 FOLLOW SYSTEM (Social Graph) ---

@app.post("/users/{target_user_id}/follow", tags=["Social Graph"])
def follow_user(target_user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id == target_user_id:
        raise HTTPException(status_code=400, detail="You cannot follow your own account profile.")
        
    target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="The user you are trying to follow does not exist.")
        
    if target_user in current_user.following:
        current_user.following.remove(target_user)
        db.commit()
        return {"message": f"Successfully unfollowed user '{target_user.username}'."}
        
    current_user.following.append(target_user)
    notification = models.Notification(content=f"User '{current_user.username}' started following you!", user_id=target_user_id)
    db.add(notification)
    db.commit()
    return {"message": f"Successfully followed user '{target_user.username}'."}


# --- 🔔 NOTIFICATIONS INBOX SYSTEM ---

@app.get("/notifications", response_model=List[schemas.NotificationResponse], tags=["Notifications System"])
def get_user_notifications(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Notification).filter(models.Notification.user_id == current_user.id).order_by(models.Notification.created_at.desc()).all()


@app.patch("/notifications/{notification_id}/read", tags=["Notifications System"])
def mark_notification_as_read(notification_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
        
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        
    notification.is_read = True
    db.commit()
    return {"status": "success", "message": f"Notification {notification_id} marked as read."}


@app.post("/notifications/read-all", tags=["Notifications System"])
def mark_all_notifications_as_read(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"status": "success", "message": "All notifications marked as read."}


# --- 👤 LIVE USER PROFILE STATS ENGINE ---

@app.get("/users/me/profile", tags=["Users Profile Management"])
async def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "followers_count": len(current_user.followers) if hasattr(current_user, "followers") else 0,
        "following_count": len(current_user.following) if hasattr(current_user, "following") else 0,
        "profile_pic_url": getattr(current_user, "profile_pic_url", "/static/defaults/default-avatar.png") or "/static/defaults/default-avatar.png"
    }


# --- 👥 USER DISCOVERY & SEARCH ENGINE ---

@app.get("/users/search", response_model=List[schemas.UserSearchResponse], tags=["Users Profile Management"])
def search_users(
    q: str = "", 
    limit: int = 10, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Search for users by username. 
    Excludes the current logged-in user from search results.
    """
    if not q:
        return []

    # Query matching usernames case-insensitively, excluding the current active user
    matching_users = db.query(models.User).filter(
        models.User.username.ilike(f"%{q}%"),
        models.User.id != current_user.id
    ).limit(limit).all()

    return matching_users
