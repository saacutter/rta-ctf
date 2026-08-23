import os
from dotenv import load_dotenv

class Config:
    # Load the environment variables from the .env file
    load_dotenv()

    # Set the secret key
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Set the database location
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "forum.db")