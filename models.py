from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

# 🔗 Many-to-Many Association Table for Followers (Renamed uniquely)
followers_association = Table(
    "followers",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("followed_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

# 🔗 Many-to-Many Association Table for Likes (Renamed uniquely)
likes_association = Table(
    "likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False) 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_verified = Column(Boolean, default=False)  
    
    verification_code = Column(String, nullable=True)
    verification_expires_at = Column(DateTime, nullable=True)

    # 🔗 Standardized ORM Relationships
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    liked_posts = relationship("Post", secondary=likes_association, back_populates="liked_by")
    
    # 🔗 Self-Referential Social Graph Links (Completely migrated to followers_association)
    following = relationship(
        "User",
        secondary=followers_association,
        primaryjoin=(id == followers_association.c.follower_id),
        secondaryjoin=(id == followers_association.c.followed_id),
        back_populates="followers"
    )
    followers = relationship(
        "User",
        secondary=followers_association,
        primaryjoin=(id == followers_association.c.followed_id),
        secondaryjoin=(id == followers_association.c.follower_id),
        back_populates="following"
    )

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    media_url = Column(String, nullable=True) 
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # 🔗 Standardized ORM Relationships
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    liked_by = relationship("User", secondary=likes_association, back_populates="liked_posts")
    
    @property
    def owner(self):
        return self.user

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))
    
    # 🔗 Standardized ORM Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # 🔗 Standardized ORM Relationships
    user = relationship("User", back_populates="notifications")