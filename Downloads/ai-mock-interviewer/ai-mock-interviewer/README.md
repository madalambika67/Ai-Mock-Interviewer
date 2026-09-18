# Green Room — AI Mock Interviewer

A full-stack AI-powered mock interview platform: register, upload a resume,
pick a role and interview type, and get asked technical, HR, behavioral, and
role-specific questions one at a time — by text or voice — with instant AI
feedback on every answer and a full performance dashboard afterward.

Built with **Flask, SQLAlchemy (SQLite or MySQL/XAMPP), Flask-Login,
vanilla JS, Chart.js, and the browser's Web Speech API** for voice
input/output. No paid API key is required to run it — see "AI scoring" below.

---

## Features

- **Auth** — register/login with hashed passwords (Flask-Login + Werkzeug)
- **Resume upload** — PDF / DOCX / TXT, parsed for skills, optional
  job-description paste for a resume-to-role match score
- **Personalized interviews** — role, interview type (technical / HR /
  behavioral / role-specific / mixed), difficulty, and question count
- **Voice or text answers** — speech-to-text via the Web Speech API
  (Chrome/Edge); "realistic interviewer mode" reads questions aloud with
  text-to-speech
- **Timed mode** — a countdown per question, auto-submits at zero
- **Instant AI feedback** — every answer is scored 0-100 on technical
  accuracy, relevance, communication, clarity, confidence, and completeness,
  with a one-line coaching note
- **AI follow-up questions** — short/thin answers automatically get a
  natural follow-up prompt
- **STAR-method feedback** — behavioral answers are checked for
  Situation / Task / Action / Result structure
- **Final report** — overall score, strengths, weaknesses, missing skills,
  a personalized improvement plan, recommended topics, and fresh practice
  questions
- **Analytics dashboard** — score trend line chart, skill-wise radar chart,
  and full interview history

## AI scoring: two modes

By default the app uses a **built-in offline heuristic AI engine**
(`utils/ai_engine.py`) — it analyzes keyword overlap with the role/question,
filler-word density, hedging language, sentence structure, and STAR-method
markers to produce the six scores. It needs no API key, no internet
connection, and no cost, which makes the whole app runnable out of the box —
ideal for a demo or a viva.

If you want real LLM-graded answers instead, set in `.env`:
```
AI_PROVIDER=openai        # or: anthropic
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```
When set, `utils/ai_engine.analyze_answer()` calls the real API for scoring
and automatically falls back to the offline engine if the call fails.

## Voice features

Speech-to-text and text-to-speech both run **entirely in the browser** via
the Web Speech API (`SpeechRecognition` / `speechSynthesis`) — no server-side
speech API, no extra cost. This works best in **Google Chrome or Microsoft
Edge**. If the browser doesn't support it, the app automatically tells the
user to type instead.

---

## Project structure

```
ai-mock-interviewer/
├── app.py                  # Flask app factory + entry point
├── config.py                # Config (reads .env)
├── models.py                 # SQLAlchemy models
├── requirements.txt
├── .env.example              # copy to .env and edit
├── data/
│   └── questions.json        # question bank by role / category / difficulty
├── database/
│   └── schema_mysql.sql      # reference schema for MySQL / XAMPP
├── routes/
│   ├── auth.py                # register / login / logout
│   ├── interview.py           # setup, live session API, results
│   └── dashboard.py           # dashboard + analytics JSON API
├── utils/
│   ├── ai_engine.py           # question generation + answer scoring + reports
│   └── resume_parser.py       # PDF/DOCX/TXT text + skill extraction
├── static/
│   ├── css/style.css          # design system
│   ├── js/                    # (all interview JS is inline in templates)
│   └── uploads/resumes/       # uploaded resumes are stored here
└── templates/
    ├── base.html, login.html, register.html
    ├── dashboard.html
    ├── interview_setup.html
    ├── interview_session.html
    └── results.html
```

---

## Setup

### 1. Requirements
- Python 3.10+
- pip

### 2. Install dependencies
```bash
cd ai-mock-interviewer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```
Open `.env` and set a `SECRET_KEY` (any random string). Everything else has
a working default.

### 4. Choose your database

**Option A — SQLite (default, zero setup).** Just leave `DB_TYPE=sqlite` in
`.env`. The app creates `instance/app.db` automatically on first run.

**Option B — MySQL / XAMPP.**
1. Start Apache + MySQL in the XAMPP control panel.
2. Create a database (phpMyAdmin, or import `database/schema_mysql.sql`
   directly — the app will also create any missing tables itself).
3. In `.env`, set:
   ```
   DB_TYPE=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_DATABASE=ai_mock_interviewer
   ```

### 5. Run
```bash
python app.py
```
Visit **http://localhost:5000** — register an account and start your first
mock interview.

---

## Notes for the portfolio write-up

- The offline AI engine is a transparent, explainable rule-based system —
  useful to point to in a viva ("here is exactly how each score is
  computed"), while still leaving room to plug in a real LLM.
- Resume skill extraction uses a curated keyword dictionary
  (`utils/resume_parser.py`) rather than a black-box NLP model, again for
  explainability.
- All voice features are client-side only (Web Speech API), so the app has
  zero dependency on a paid speech-to-text/text-to-speech service.
- The schema supports both SQLite and MySQL through the same SQLAlchemy
  models — switching is a single `.env` value.

## Possible extensions

- Add OAuth login (Google/GitHub)
- Export the final report as a PDF
- Add a webcam-based confidence/eye-contact estimator for "realistic mode"
- Support multiple resumes per user with a resume comparison view
- Add an admin view to curate/expand the question bank
