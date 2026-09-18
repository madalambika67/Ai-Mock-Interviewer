import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    DB_TYPE = os.environ.get("DB_TYPE", "sqlite")

    if DB_TYPE == "mysql":
        MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
        MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
        MYSQL_USER = os.environ.get("MYSQL_USER", "root")
        MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
        MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "ai_mock_interviewer")
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:"
            f"{MYSQL_PORT}/{MYSQL_DATABASE}"
        )
    else:
        os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/app.db

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads", "resumes")
    ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx", "txt"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

    AI_PROVIDER = os.environ.get("AI_PROVIDER", "").strip().lower()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
