from app import db, login
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import List

@login.user_loader
def load_user(id):
    return Users.query.get(id)

class Users(db.Model, UserMixin):
    id = mapped_column(db.Integer, primary_key=True)
    username = mapped_column(db.Text, unique=True, nullable=False, index=True)
    email = mapped_column(db.Text, unique=True, nullable=False)
    password = mapped_column(db.String(60), nullable=False) # bcrypt hashes are 60 characters wide
    posts = db.relationship('Posts', back_populates='author_obj', foreign_keys='Posts.author')
    comments = db.relationship('Comments', back_populates='author_obj', foreign_keys='Comments.author')

class Posts(db.Model):
    id = mapped_column(db.Integer, primary_key=True)
    title = mapped_column(db.Text)
    body = mapped_column(db.Text)
    author = mapped_column(db.Integer, db.ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    author_obj = db.relationship('Users', back_populates='posts', foreign_keys=[author])
    comments = db.relationship('Comments', back_populates='post_obj', foreign_keys='Comments.post')

class Comments(db.Model):
    id = mapped_column(db.Integer, primary_key=True)
    post = mapped_column(db.Integer, db.ForeignKey('posts.id'))
    author = mapped_column(db.Integer, db.ForeignKey('users.id'))
    body = mapped_column(db.Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    author_obj = db.relationship('Users', back_populates='comments', foreign_keys=[author])
    post_obj = db.relationship('Posts', back_populates='comments', foreign_keys=[post])