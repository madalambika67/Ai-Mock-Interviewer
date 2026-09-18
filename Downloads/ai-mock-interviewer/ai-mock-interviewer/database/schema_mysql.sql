-- ============================================================
-- AI Mock Interviewer — MySQL schema (for XAMPP / phpMyAdmin)
--
-- You do NOT need to run this file by hand: when DB_TYPE=mysql
-- is set in .env, the Flask app (via SQLAlchemy) creates all of
-- these tables automatically on first run.
--
-- This file is provided for reference, for importing directly
-- through phpMyAdmin, or for anyone who prefers to inspect /
-- version-control the schema explicitly.
-- ============================================================

CREATE DATABASE IF NOT EXISTS ai_mock_interviewer
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_mock_interviewer;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS resumes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  filename VARCHAR(255) NOT NULL,
  raw_text LONGTEXT,
  extracted_skills TEXT,
  job_description TEXT,
  match_score FLOAT DEFAULT 0,
  uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interviews (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  resume_id INT NULL,
  job_role VARCHAR(150) NOT NULL,
  interview_type VARCHAR(50) NOT NULL,
  difficulty VARCHAR(20) DEFAULT 'medium',
  mode VARCHAR(20) DEFAULT 'text',
  timed_mode BOOLEAN DEFAULT FALSE,
  realistic_mode BOOLEAN DEFAULT FALSE,
  seconds_per_question INT DEFAULT 90,
  status VARCHAR(20) DEFAULT 'in_progress',
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  overall_score FLOAT DEFAULT 0,
  technical_score FLOAT DEFAULT 0,
  communication_score FLOAT DEFAULT 0,
  confidence_score FLOAT DEFAULT 0,
  clarity_score FLOAT DEFAULT 0,
  completeness_score FLOAT DEFAULT 0,
  relevance_score FLOAT DEFAULT 0,
  strengths TEXT,
  weaknesses TEXT,
  missing_skills TEXT,
  improvement_plan TEXT,
  recommended_topics TEXT,
  practice_questions TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interview_questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  interview_id INT NOT NULL,
  order_index INT NOT NULL,
  question_text TEXT NOT NULL,
  category VARCHAR(50),
  difficulty VARCHAR(20),
  is_follow_up BOOLEAN DEFAULT FALSE,
  answer_text TEXT,
  answer_time_seconds INT,
  input_mode VARCHAR(20) DEFAULT 'text',
  technical_accuracy FLOAT,
  relevance FLOAT,
  communication FLOAT,
  clarity FLOAT,
  confidence FLOAT,
  completeness FLOAT,
  star_feedback TEXT,
  question_score FLOAT,
  feedback TEXT,
  answered_at DATETIME NULL,
  FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
) ENGINE=InnoDB;
