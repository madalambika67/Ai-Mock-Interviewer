from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resumes = db.relationship("Resume", backref="user", lazy=True, cascade="all, delete-orphan")
    interviews = db.relationship("Interview", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text)
    extracted_skills = db.Column(db.Text)   # JSON-encoded list
    job_description = db.Column(db.Text)    # optional pasted JD
    match_score = db.Column(db.Float, default=0.0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=True)

    job_role = db.Column(db.String(150), nullable=False)
    interview_type = db.Column(db.String(50), nullable=False)   # technical/hr/behavioral/role-specific/mixed
    difficulty = db.Column(db.String(20), default="medium")     # easy/medium/hard
    mode = db.Column(db.String(20), default="text")             # text/voice
    timed_mode = db.Column(db.Boolean, default=False)
    realistic_mode = db.Column(db.Boolean, default=False)
    seconds_per_question = db.Column(db.Integer, default=90)

    status = db.Column(db.String(20), default="in_progress")    # in_progress/completed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    overall_score = db.Column(db.Float, default=0.0)
    technical_score = db.Column(db.Float, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    confidence_score = db.Column(db.Float, default=0.0)
    clarity_score = db.Column(db.Float, default=0.0)
    completeness_score = db.Column(db.Float, default=0.0)
    relevance_score = db.Column(db.Float, default=0.0)

    strengths = db.Column(db.Text)          # JSON list
    weaknesses = db.Column(db.Text)         # JSON list
    missing_skills = db.Column(db.Text)     # JSON list
    improvement_plan = db.Column(db.Text)   # JSON list
    recommended_topics = db.Column(db.Text) # JSON list
    practice_questions = db.Column(db.Text) # JSON list

    questions = db.relationship("InterviewQuestion", backref="interview", lazy=True,
                                 cascade="all, delete-orphan", order_by="InterviewQuestion.order_index")


class InterviewQuestion(db.Model):
    __tablename__ = "interview_questions"

    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)

    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))       # technical/hr/behavioral/role-specific
    difficulty = db.Column(db.String(20))
    is_follow_up = db.Column(db.Boolean, default=False)

    answer_text = db.Column(db.Text)
    answer_time_seconds = db.Column(db.Integer)
    input_mode = db.Column(db.String(20), default="text")  # text/voice

    technical_accuracy = db.Column(db.Float)
    relevance = db.Column(db.Float)
    communication = db.Column(db.Float)
    clarity = db.Column(db.Float)
    confidence = db.Column(db.Float)
    completeness = db.Column(db.Float)
    star_feedback = db.Column(db.Text)        # JSON dict for behavioral answers
    question_score = db.Column(db.Float)
    feedback = db.Column(db.Text)

    answered_at = db.Column(db.DateTime)
