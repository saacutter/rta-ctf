from app.blueprints import blueprint
from app import db, models, forms
from flask import render_template, request, redirect, url_for, jsonify, abort, current_app
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from datetime import datetime, timezone
import os


@blueprint.route("/")
@login_required
def index():
    # Retrieve all the posts
    posts = models.Posts.query.join(models.Users, models.Posts.author == models.Users.id).order_by(models.Posts.created_at.desc()).all()

    return render_template("index.html", posts=posts)


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    # Ensure that the user cannot access this route if they are already signed in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Extract the next page from the URL and add it to the form
    if request.method == "GET":
        next_page = 'main.' + request.args.get('next', '')
        if next_page == "main./": next_page = "main.index"

    form = forms.LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        # Retrieve the user from the database based on the provided username/email address
        username = form.username.data.lower().strip()
        user = db.session.scalar(sa.select(models.Users).where((sa.func.lower(models.Users.username) == username) | (models.Users.email == username)))

        # Ensure that the user exists and that the password matches
        if user is None or form.password.data != user.password:
            return redirect(url_for('main.login'))

        # Log the user in
        login_user(user, remember=form.remember_user.data)

        # Extract the next page from the form and redirect them to that page
        next_page = request.form.get('next')
        return redirect(url_for(next_page))
    return render_template("login.html", form=form, next=next_page)


@blueprint.route('/signout')
def signout():
    logout_user()
    return redirect(url_for('main.index'))


@blueprint.route("/post/<int:post_id>")
def post_detail(post_id):
    # Retrieve the post from the database
    post = db.first_or_404(sa.select(models.Posts).where(models.Posts.id == post_id))

    # Retrieve the comments on the post
    comments = models.Comments.query.join(models.Posts, models.Comments.post == models.Posts.id).join(models.Users, models.Comments.author == models.Users.id).where(models.Comments.post == post_id).order_by(models.Comments.created_at.desc()).all()

    return render_template("post.html", post=post, comments=comments)


# @blueprint.route("/post/<int:post_id>/comment", methods=["POST"])
# def add_comment(post_id):
#     # db = get_db()
#     # post = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
#     if post is None:
#         abort(404)
#     body = (request.form.get("body")).strip()
#     # db.execute(
#     #     "INSERT INTO comments (post_id, author, body, created_at) VALUES (?, ?, ?, ?)",
#     #     (post_id, author, body, datetime.utcnow().isoformat()),
#     # )
#     # db.commit()
#     return redirect(url_for("post_detail", post_id=post_id))


# @blueprint.route("/submit", methods=["POST"])
# def submit():
#     # db = get_db()
#     if request.method == "POST":
#         title = (request.form.get("title") or "").strip()
#         body = (request.form.get("body") or "").strip()
#         author = (request.form.get("author") or "").strip()[:40]
#         # cur = db.execute(
#         #     "INSERT INTO posts title, body, author, created_at) VALUES (?, ?, ?, ?)",
#         #     (title, body, author, datetime.utcnow().isoformat()),
#         # )
#         # db.commit()
#         return redirect(url_for("post_detail", post_id=cur.lastrowid))
#     return render_template("create_post.html", form={})


@blueprint.app_template_filter("timeago")
def timeago(value):
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    seconds = int((datetime.utcnow() - dt).total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"
