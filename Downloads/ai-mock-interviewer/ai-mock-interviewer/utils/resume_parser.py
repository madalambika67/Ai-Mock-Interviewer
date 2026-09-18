"""
Resume parsing utilities.

Extracts raw text from PDF / DOCX / TXT resumes and detects likely skills
using a curated keyword dictionary. This is a lightweight, dependency-free
(besides PyPDF2 / python-docx) approach that works well for a portfolio
project without needing a paid NLP API.
"""
import os
import re

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "mysql", "postgresql",
    "mongodb", "html", "css", "react", "angular", "vue", "node.js", "node", "flask", "django",
    "spring boot", "express", "rest api", "graphql", "git", "github", "docker", "kubernetes",
    "aws", "azure", "gcp", "linux", "machine learning", "deep learning", "data structures",
    "algorithms", "oop", "system design", "agile", "scrum", "excel", "power bi", "tableau",
    "pandas", "numpy", "tensorflow", "pytorch", "testing", "unit testing", "ci/cd",
    "communication", "leadership", "teamwork", "problem solving", "time management",
    "project management", "stakeholder management", "user research", "roadmapping",
    "statistics", "data visualization", "android", "kotlin", "swift", "flutter", "php",
    "laravel", "redux", "next.js", "figma", "ui/ux", "networking", "cybersecurity",
]


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def extract_text(filepath):
    ext = filepath.rsplit(".", 1)[1].lower()
    try:
        if ext == "pdf":
            return _extract_pdf(filepath)
        elif ext == "docx":
            return _extract_docx(filepath)
        elif ext == "txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        return f""
    return ""


def _extract_pdf(filepath):
    from PyPDF2 import PdfReader
    text = []
    reader = PdfReader(filepath)
    for page in reader.pages:
        content = page.extract_text() or ""
        text.append(content)
    return "\n".join(text)


def _extract_docx(filepath):
    import docx
    doc = docx.Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_skills(text):
    if not text:
        return []
    lowered = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, lowered):
            found.append(skill)
    return found


def calculate_match_score(resume_skills, job_description_text, role_skills=None):
    """
    Rough resume <-> job description / role match percentage based on
    keyword overlap. Returns a 0-100 float.
    """
    resume_skill_set = set(s.lower() for s in resume_skills)

    target_skills = set()
    if job_description_text:
        target_skills |= set(s.lower() for s in extract_skills(job_description_text))
    if role_skills:
        target_skills |= set(s.lower() for s in role_skills)

    if not target_skills:
        return 0.0

    overlap = resume_skill_set & target_skills
    score = (len(overlap) / len(target_skills)) * 100
    return round(min(score, 100.0), 1)
