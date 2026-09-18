import json
import os
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import db, Resume, Interview, InterviewQuestion
from utils import resume_parser, ai_engine

interview_bp = Blueprint("interview", __name__, url_prefix="/interview")

ROLE_CHOICES = list(ai_engine.QUESTION_BANK["roles"].keys())


@interview_bp.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        job_role = request.form.get("job_role") or "General / Other"
        interview_type = request.form.get("interview_type", "mixed")
        difficulty = request.form.get("difficulty", "medium")
        mode = request.form.get("mode", "text")
        num_questions = int(request.form.get("num_questions", 6))
        timed_mode = request.form.get("timed_mode") == "on"
        realistic_mode = request.form.get("realistic_mode") == "on"
        seconds_per_question = int(request.form.get("seconds_per_question", 90))
        job_description = request.form.get("job_description", "").strip()

        resume_id = None
        resume_skills = []

        uploaded_file = request.files.get("resume_file")
        if uploaded_file and uploaded_file.filename:
            if not resume_parser.allowed_file(uploaded_file.filename, current_app.config["ALLOWED_RESUME_EXTENSIONS"]):
                flash("Unsupported resume file type. Please upload a PDF, DOCX, or TXT file.", "error")
                return redirect(url_for("interview.setup"))

            filename = secure_filename(f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{uploaded_file.filename}")
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            uploaded_file.save(filepath)

            raw_text = resume_parser.extract_text(filepath)
            skills = resume_parser.extract_skills(raw_text)
            role_data = ai_engine.get_role_data(job_role)
            match_score = resume_parser.calculate_match_score(skills, job_description, role_data.get("skills"))

            resume = Resume(
                user_id=current_user.id, filename=filename, raw_text=raw_text,
                extracted_skills=json.dumps(skills), job_description=job_description or None,
                match_score=match_score,
            )
            db.session.add(resume)
            db.session.commit()
            resume_id = resume.id
            resume_skills = skills

        interview = Interview(
            user_id=current_user.id, resume_id=resume_id, job_role=job_role,
            interview_type=interview_type, difficulty=difficulty, mode=mode,
            timed_mode=timed_mode, realistic_mode=realistic_mode,
            seconds_per_question=seconds_per_question, status="in_progress",
        )
        db.session.add(interview)
        db.session.commit()

        questions = ai_engine.build_interview_questions(
            job_role, interview_type, difficulty, num_questions=num_questions, resume_skills=resume_skills
        )
        for q in questions:
            iq = InterviewQuestion(
                interview_id=interview.id, order_index=q["order_index"], question_text=q["text"],
                category=q["category"], difficulty=q["difficulty"], input_mode=mode,
            )
            db.session.add(iq)
        db.session.commit()

        return redirect(url_for("interview.session_view", interview_id=interview.id))

    recent_resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).limit(5).all()
    return render_template("interview_setup.html", roles=ROLE_CHOICES, recent_resumes=recent_resumes)


@interview_bp.route("/<int:interview_id>/session")
@login_required
def session_view(interview_id):
    interview = Interview.query.filter_by(id=interview_id, user_id=current_user.id).first_or_404()
    if interview.status == "completed":
        return redirect(url_for("interview.results", interview_id=interview.id))
    questions = [
        {"order_index": q.order_index, "text": q.question_text, "category": q.category, "difficulty": q.difficulty}
        for q in interview.questions
    ]
    return render_template("interview_session.html", interview=interview, questions_json=json.dumps(questions))


@interview_bp.route("/<int:interview_id>/answer", methods=["POST"])
@login_required
def submit_answer(interview_id):
    interview = Interview.query.filter_by(id=interview_id, user_id=current_user.id).first_or_404()
    data = request.get_json(force=True)
    order_index = data.get("order_index")
    answer_text = (data.get("answer_text") or "").strip()
    time_taken = data.get("time_taken")
    input_mode = data.get("input_mode", "text")
    is_follow_up_response = data.get("is_follow_up_response", False)

    iq = InterviewQuestion.query.filter_by(interview_id=interview.id, order_index=order_index).first()
    if not iq:
        return jsonify({"error": "Question not found"}), 404

    resume_skills = []
    if interview.resume_id:
        resume = Resume.query.get(interview.resume_id)
        if resume and resume.extracted_skills:
            resume_skills = json.loads(resume.extracted_skills)
    role_skills = ai_engine.get_role_data(interview.job_role).get("skills", [])
    all_skills = list(set(resume_skills) | set(role_skills))

    if is_follow_up_response and iq.answer_text:
        combined_answer = iq.answer_text + " " + answer_text
    else:
        combined_answer = answer_text

    analysis = ai_engine.analyze_answer(
        iq.question_text, combined_answer, iq.category, all_skills,
        ai_provider=current_app.config.get("AI_PROVIDER"),
        api_key=(current_app.config.get("OPENAI_API_KEY") if current_app.config.get("AI_PROVIDER") == "openai"
                 else current_app.config.get("ANTHROPIC_API_KEY")),
        time_taken=time_taken, seconds_allotted=interview.seconds_per_question if interview.timed_mode else None,
    )

    iq.answer_text = combined_answer
    iq.answer_time_seconds = time_taken
    iq.input_mode = input_mode
    iq.technical_accuracy = analysis["technical_accuracy"]
    iq.relevance = analysis["relevance"]
    iq.communication = analysis["communication"]
    iq.clarity = analysis["clarity"]
    iq.confidence = analysis["confidence"]
    iq.completeness = analysis["completeness"]
    iq.question_score = analysis["question_score"]
    iq.feedback = analysis["feedback"]
    iq.star_feedback = json.dumps(analysis["star_feedback"]) if analysis.get("star_feedback") else None
    iq.answered_at = datetime.utcnow()
    db.session.commit()

    follow_up = None
    if not is_follow_up_response and combined_answer:
        follow_up = ai_engine.generate_follow_up(iq.question_text, combined_answer)

    return jsonify({
        "score": analysis["question_score"],
        "feedback": analysis["feedback"],
        "breakdown": {
            "Technical Accuracy": analysis["technical_accuracy"], "Relevance": analysis["relevance"],
            "Communication": analysis["communication"], "Clarity": analysis["clarity"],
            "Confidence": analysis["confidence"], "Completeness": analysis["completeness"],
        },
        "star_feedback": analysis.get("star_feedback"),
        "follow_up": follow_up,
    })


@interview_bp.route("/<int:interview_id>/complete", methods=["POST"])
@login_required
def complete_interview(interview_id):
    interview = Interview.query.filter_by(id=interview_id, user_id=current_user.id).first_or_404()

    resume_skills = []
    if interview.resume_id:
        resume = Resume.query.get(interview.resume_id)
        if resume and resume.extracted_skills:
            resume_skills = json.loads(resume.extracted_skills)

    questions_data = [{
        "question_score": q.question_score, "technical_accuracy": q.technical_accuracy,
        "relevance": q.relevance, "communication": q.communication, "clarity": q.clarity,
        "confidence": q.confidence, "completeness": q.completeness, "answer_text": q.answer_text,
    } for q in interview.questions]

    report = ai_engine.generate_final_report(interview.job_role, questions_data, resume_skills)

    interview.overall_score = report["overall_score"]
    interview.technical_score = report["technical_score"]
    interview.communication_score = report["communication_score"]
    interview.confidence_score = report["confidence_score"]
    interview.clarity_score = report["clarity_score"]
    interview.completeness_score = report["completeness_score"]
    interview.relevance_score = report["relevance_score"]
    interview.strengths = json.dumps(report["strengths"])
    interview.weaknesses = json.dumps(report["weaknesses"])
    interview.missing_skills = json.dumps(report["missing_skills"])
    interview.improvement_plan = json.dumps(report["improvement_plan"])
    interview.recommended_topics = json.dumps(report["recommended_topics"])
    interview.practice_questions = json.dumps(report["practice_questions"])
    interview.status = "completed"
    interview.completed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"redirect": url_for("interview.results", interview_id=interview.id)})


@interview_bp.route("/<int:interview_id>/results")
@login_required
def results(interview_id):
    interview = Interview.query.filter_by(id=interview_id, user_id=current_user.id).first_or_404()
    if interview.status != "completed":
        return redirect(url_for("interview.session_view", interview_id=interview.id))

    context = {
        "interview": interview,
        "strengths": json.loads(interview.strengths or "[]"),
        "weaknesses": json.loads(interview.weaknesses or "[]"),
        "missing_skills": json.loads(interview.missing_skills or "[]"),
        "improvement_plan": json.loads(interview.improvement_plan or "[]"),
        "recommended_topics": json.loads(interview.recommended_topics or "[]"),
        "practice_questions": json.loads(interview.practice_questions or "[]"),
    }
    return render_template("results.html", **context)
