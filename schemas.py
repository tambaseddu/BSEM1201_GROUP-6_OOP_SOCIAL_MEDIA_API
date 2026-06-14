from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

# ==========================================
# 1. USER SCHEMAS (Keep these at the top)
# ==========================================
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None  # ✅ Added for profile bio updates
    is_admin: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_admin: bool
    bio: Optional[str] = None  # ✅ Included in full profile views
    followers_count: int = 0
    following_count: int = 0
    created_at: datetime.datetime
    class Config:
        from_attributes = True

class UserMinified(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None  # ✅ Included so we can read bios inside feed lookups
    followers_count: int = 0
    following_count: int = 0
    class Config:
        from_attributes = True


# ==========================================
# 2. TOKEN SCHEMAS
# ==========================================
class Token(BaseModel):
    access_token: str
    token_type: str


# ==========================================
# 3. COMMENT SCHEMAS (Below UserMinified)
# ==========================================
class CommentCreate(BaseModel):
    content: str

class CommentUpdate(BaseModel):  # ✏️ NEW: Validates incoming comment edit data payloads
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    created_at: datetime.datetime
    user: UserMinified  
    class Config:
        from_attributes = True

# ==========================================
# NOTIFICATION SCHEMAS
# ==========================================
class NotificationResponse(BaseModel):
    id: int
    content: str
    is_read: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ==========================================
# 4. POST SCHEMAS (Below CommentResponse)
# ==========================================
class PostCreate(BaseModel):
    content: str
    media_url: Optional[str] = None

class PostUpdate(BaseModel):  # ✏️ NEW: Validates incoming post edit content
    content: str

class PostResponse(BaseModel):
    id: int
    content: str
    media_url: Optional[str] = None
    like_count: int
    created_at: datetime.datetime
    user: UserMinified  
    comments: List[CommentResponse] = []  
    class Config:
        from_attributes = True

# 5 SEARCH FOR USERS SCHEMA
class UserSearchResponse(BaseModel):
    id: int
    username: str
    profile_pic_url: Optional[str] = None

    class Config:
        from_attributes = True